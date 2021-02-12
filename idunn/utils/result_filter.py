import logging
import re
from typing import List
from unidecode import unidecode

from jellyfish import damerau_levenshtein_distance


logger = logging.getLogger(__name__)


# Typical suffixes found after numbers such as "4bis", "4th", ...
NUM_SUFFIXES = ["bis", "ter", "quad", "e", "è", "eme", "ème", "er", "st", "nd", "rd", "th"]

# Abrevation typical found in places, addresses, ...
ABREVIATIONS = {
    "av": "avenue",
    "bd": "boulevard",
    "r": "rue",
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
        if word.lower().endswith(suffix):
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

    return word_matches_abreviation(query_word.lower(), label_word.lower()) or any(
        damerau_levenshtein_distance(query_word.lower(), s) <= 1
        for s in [label_word.lower(), unidecode(label_word.lower())]
    )


def check(
    query: str,
    name: str,
    admins: List[str] = [],
    postcodes: List[str] = [],
    is_address: bool = True,
) -> bool:
    query_words = words(query)
    name_words = words(name)

    if is_address:
        query_words = [word for word in query_words if word.lower() not in NUM_SUFFIXES]

    # Check if all words of the query match a word in the result
    full_label = [
        *words(name),
        *postcodes,
        *(w for admin in admins for w in words(admin)),
    ]

    for q_word in query_words:
        if not any(word_matches(q_word, l_word) for l_word in full_label):
            logger.info(
                "Removed `%s` from results because queried `%s` does not match the result",
                name,
                q_word,
            )
            return False

    # Check if at least 2/3 of the result's name is covered by the query
    def coverage(terms):
        return sum(
            any(word_matches(query_word, term) for query_word in query_words) for term in terms
        ) / len(terms)

    check_coverage = any(
        coverage(terms) >= (2 / 3)
        for terms in [
            name_words,
            *[name_words + words(admin) for admin in admins],
            *[name_words + [postcode] for postcode in postcodes],
        ]
    )

    if not check_coverage:
        logger.info(
            "Removed `%s` from results because query `%s` is not accurate enough", name, query,
        )
        return False

    return True


def check_bragi_response(query: str, bragi_response: dict) -> bool:
    """
    Filter a feature from bragi responses, please provide the field
    bragi_response["features"][..]["properties"]["geocoding"].
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

    return check(
        query,
        bragi_response["name"],
        [admin["name"] for admin in bragi_response.get("administrative_regions", [])],
        postcodes,
        bragi_response.get("type") == "address",
    )
