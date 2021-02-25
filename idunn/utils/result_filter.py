import logging
import re
from functools import lru_cache
from typing import List, Optional
from unidecode import unidecode

from jellyfish import damerau_levenshtein_distance


logger = logging.getLogger(__name__)


# Typical suffixes found after numbers such as "4bis", "4th", ...
NUM_SUFFIXES = ["bis", "ter", "quad", "e", "è", "eme", "ème", "er", "st", "nd", "rd", "th"]

# Abrevation typical found in places, addresses, ...
ABREVIATIONS = {
    "av": "avenue",
    "bd": "boulevard",
    "bld": "boulevard",
    "bvd": "boulevard",
    "rle": "ruelle",
    "r": "rue",
    "rte": "route",
    "ste": "sainte",
    "st": "saint",
}


def words(text):
    """
    Split words into a list.

    >>> words("17, rue jaune ; Levallois-Peret")
    ['17', 'rue', 'jaune', 'Levallois', 'Peret']
    """
    separators = [" ", "-", ",", ";", "\\.", "'"]
    return [word for word in re.split("|".join(separators), text) if word]


def word_as_number(word):
    """
    Attempt to intepret the word as a number, potentialy triming a suffix.

    >>> word_as_number("17")
    '17'
    >>> word_as_number("17bis")
    '17'
    >>> assert word_as_number("17rue") is None
    """
    if word.isnumeric():
        return word

    for suffix in NUM_SUFFIXES:
        if word.endswith(suffix):
            prefix = word[: -len(suffix)]

            if prefix.isnumeric():
                return prefix

    return None


def word_matches_abreviation(word_1, word_2):
    """
    Check if a word is the abreviation of the other.

    >>> assert word_matches_abreviation("bd", "boulevard")
    >>> assert word_matches_abreviation("avenue", "av")
    >>> assert not word_matches_abreviation("av", "bd")
    """
    return ABREVIATIONS.get(word_1) == word_2 or ABREVIATIONS.get(word_2) == word_1


@lru_cache(10000)
def word_matches(query_word, label_word):
    """
    Check if two words match with an high degree of confidence.

    A single spelling mistake is allowed, defined as either a wrong letter
    (insertion, deletion or replaced) or the inversion of two consecutive
    letters. If an accent is defined in the query, then it must appear in
    the result (or it will count as a spelling mistake). Abreviations are
    supported as defined in word_matches_abreviation.

    Numbers have a special treatment: if word from the query is a number
    (without potential suffix), then it must exactly match the word from
    the result (a number, potentialy with suffix removed).

    >>> assert word_matches("42ter", "42")
    >>> assert word_matches("42ter", "42bis")
    >>> assert not word_matches("321", "322")
    >>> assert not word_matches("5", "u")
    >>> assert not word_matches("u", "5")

    >>> assert word_matches("eiffel", "ieffel")
    >>> assert not word_matches("eiffel", "ifefel")
    >>> assert word_matches("eveque", "évêque")
    >>> assert not word_matches("évêque", "eveque")

    >>> assert word_matches("bd", "boulevard")
    """
    query_word_as_num = word_as_number(query_word)
    label_word_as_num = word_as_number(label_word)

    if query_word_as_num is not None or label_word_as_num is not None:
        return query_word_as_num == label_word_as_num

    return word_matches_abreviation(query_word, label_word) or any(
        damerau_levenshtein_distance(query_word, s) <= 1
        for s in [label_word, unidecode(label_word)]
    )


def count_adj_in_same_block(terms: List[str], blocks: List[List[str]]) -> int:
    """
    Count the number of consecutive terms that both match a word in a same
    block.

    >>> count_adj_in_same_block(
    ...     ["rue", "de", "paris", "lille"],
    ...     [["rue", "de", "paris"], ["lille"]],
    ... )
    2
    >>> count_adj_in_same_block(
    ...     ["rue", "de", "paris", "lille"],
    ...     [["rue", "de", "lille"], ["paris"]],
    ... )
    1
    """

    def contains(word: str, block: List[str]) -> bool:
        return any(word_matches(word, block_word) for block_word in block)

    return sum(
        any(contains(word_1, block) and contains(word_2, block) for block in blocks)
        for word_1, word_2 in zip(terms[:-1], terms[1:])
    )


def rank(
    query: str,
    names: List[str],
    admins: List[str] = [],
    postcodes: List[str] = [],
    is_address: bool = False,
    is_street: bool = False,
) -> Optional[float]:
    query_words = words(query.lower())
    names = list(map(str.lower, names))
    admins = list(map(str.lower, admins))

    if is_address:
        query_words = [word for word in query_words if word not in NUM_SUFFIXES]

    # Check if all words of the query match a word in the result
    full_label = [
        *(w for name in names for w in words(name)),
        *postcodes,
        *(w for admin in admins for w in words(admin)),
    ]

    for q_word in query_words:
        if not any(word_matches(q_word, l_word) for l_word in full_label):
            logger.info(
                "Removed `%s` from results because queried `%s` does not match the result",
                names[0],
                q_word,
            )
            return None

    # Check if at least 2/3 of the result is covered by the query in one of these cases:
    #   - over one of the result names
    #   - over one of the result names together with one of the admin names
    #   - over one of the result names together with a postcode
    def coverage(terms):
        return sum(
            any(word_matches(query_word, term) for query_word in query_words) for term in terms
        ) / len(terms)

    check_coverage = any(
        coverage(terms) >= (2 / 3)
        for name_words in map(words, names)
        for terms in [
            name_words,
            *[name_words + words(admin) for admin in admins],
            *[name_words + [postcode] for postcode in postcodes],
        ]
    )

    if not check_coverage:
        logger.info(
            "Removed `%s` from results because query `%s` is not accurate enough",
            names[0],
            query,
        )
        return None

    if (is_street or is_address) and len(query_words) > 1:
        # Count the number of adjacent words from the query which are both
        # part of a same field. The intention is to avoid swapping words
        # between name and admin.
        # (eg. "rue de Rennes, Paris" vs. "rue de Paris", Rennes)
        rank_val = (
            count_adj_in_same_block(
                query_words,
                [*map(words, names), *map(words, admins)],
            )
            / (len(query_words) - 1)
        )
    else:
        rank_val = 1.0

    return rank_val


def check(*args, **kwargs) -> bool:
    return rank(*args, **kwargs) is not None


def rank_bragi_response(query: str, bragi_response: dict) -> Optional[float]:
    """
    Filter a feature from bragi responses, please provide the field
    bragi_response["features"][..]["properties"]["geocoding"].

    If the response doesn't match, return None, overwise return an
    indicative relevance that takes value in [0, 1.0].
    """
    if bragi_response.get("postcode"):
        postcodes = bragi_response["postcode"].split(";")
    else:
        postcodes = list(
            {
                zip
                for admin in bragi_response.get("administrative_regions", [])
                for zip in admin.get("zip_codes", [])
            }
        )

    name = bragi_response["name"]
    local_names = [
        prop["value"]
        for prop in bragi_response.get("properties", [])
        if prop["key"].startswith("name:") or prop["key"].startswith("alt_name:")
    ]

    return rank(
        query,
        [name] + local_names,
        [admin["name"] for admin in bragi_response.get("administrative_regions", [])],
        postcodes,
        bragi_response.get("type") == "address",
        bragi_response.get("type") == "street",
    )


def check_bragi_response(query: str, bragi_response: dict) -> bool:
    """
    Filter a feature from bragi responses, please provide the field
    bragi_response["features"][..]["properties"]["geocoding"].
    """
    return rank_bragi_response(query, bragi_response) is not None
