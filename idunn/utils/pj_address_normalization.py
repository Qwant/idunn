# https://www.sirene.fr/sirene/public/variable/typvoie
import re

SHORTCUT_STREET_SUFFIX = {
    "All": "allée",
    "Av": "avenue",
    "Ave": "avenue",
    "Bât": "bâtiment",
    "Bat": "batiment",
    "Bld": "boulevard",
    "Bd": "boulevard",
    "Car": "carrefour",
    "Chs": "chaussée",
    "Chem": "chemin",
    "Cite": "cité",
    "Cial": "commercial",
    "Ccal": "centre commercial",
    "Cor": "corniche",
    "Crs": "cours",
    "Dom": "domaine",
    "Dsc": "descente",
    "Eca": "ecart",
    "Esp": "esplanade",
    "Fbg": "faubourg",
    "Ham": "hameau",
    "Hle": "halle",
    "Imm": "immeuble",
    "Imp": "impasse",
    "Ld": "lieu-dit",
    "Lot": "lotissement",
    "Mar": "marché",
    "Mte": "montée",
    "Pas": "passage",
    "Pl": "place",
    "Pln": "plaine",
    "Plt": "plateau",
    "Prom": "promenade",
    "Prv": "parvis",
    "Qua": "quartier",
    "Quai": "quai",
    "R": "rue",
    "Rpt": "rond-point",
    "Rle": "ruelle",
    "Roc": "rocade",
    "Rte": "route",
    "Sen": "sentier",
    "Sq": "square",
    "Tpl": "terre-plein",
    "Tra": "traverse",
    "Vla": "villa",
    "Vlge": "village",
    "Zac": "z.a.c.",
}

SHORTCUT_TITLE = {
    "St": "Saint",
    "Ste": "Sainte",
    "Gén": "Général",
    "Mar": "Maréchal",
    "Doct": "Docteur",
}

REGEX_FIND_TITLES = re.compile(
    rf"(.*?)\s({'|'.join(list(SHORTCUT_TITLE))})\s(.*)", flags=re.IGNORECASE
)


def normalized_pj_address(street_address: str) -> str:
    """
    PagesJaunes provides uncompleted street suffixes (e.g 'r' for 'rue') and titles
    (e.g 'St' for 'Saint').
    The goal is to complete address names and to normalize capitalization.
    """
    if street_address is None:
        return ""

    street_address = _check_titles_shortcut(street_address)
    street_address = _check_street_suffix_shortcut(street_address)

    return street_address


def _check_street_suffix_shortcut(street_address: str) -> str:
    temp_split = street_address.title().split()
    for idx, element in enumerate(temp_split):
        if element in SHORTCUT_STREET_SUFFIX:
            temp_split[idx] = SHORTCUT_STREET_SUFFIX[element]
            break
        if element.lower() in SHORTCUT_STREET_SUFFIX.values():
            temp_split[idx] = element.lower()
            break
    return " ".join(temp_split)


def _check_titles_shortcut(street_address: str) -> str:
    regex_match = REGEX_FIND_TITLES.match(street_address)
    if regex_match is not None:
        street_address = re.sub(
            REGEX_FIND_TITLES,
            rf"\1 {SHORTCUT_TITLE[regex_match.group(2).title()]} \3",
            street_address.title(),
            count=1,
        )
    return street_address
