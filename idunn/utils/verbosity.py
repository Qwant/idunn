from enum import Enum

from idunn.blocks import (
    Weather,
    ContactBlock,
    DescriptionEvent,
    GradesBlock,
    ImagesBlock,
    InformationBlock,
    OpeningDayEvent,
    OpeningHourBlock,
    Covid19Block,
    PhoneBlock,
    RecyclingBlock,
    WebSiteBlock,
    TransactionalBlock,
    SocialBlock,
    DescriptionBlock,
    DeliveryBlock,
    StarsBlock,
)


def get_name(properties, lang):
    """
    Return the Place name from the properties field of the elastic response. Here 'name'
    corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

    If lang is None or if name:lang is not in the properties then name receives the local name
    value.

    >>> get_name({}, 'fr') is None
    True

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, None)
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'cz')
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'fr')
    'spontinifr'
    """
    name = properties.get(f"name:{lang}")
    if name is None:
        name = properties.get("name")
    return name


class Verbosity(str, Enum):
    """
    Control the verbosity of the output.
    """

    LONG = "long"
    SHORT = "short"
    LIST = "list"

    @classmethod
    def default(cls):
        return cls.LONG

    @classmethod
    def default_list(cls):
        return cls.LIST


BLOCKS_BY_VERBOSITY = {
    Verbosity.LONG: [
        Weather,
        OpeningDayEvent,
        DescriptionEvent,
        OpeningHourBlock,
        Covid19Block,
        PhoneBlock,
        InformationBlock,
        WebSiteBlock,
        ContactBlock,
        ImagesBlock,
        GradesBlock,
        RecyclingBlock,
        TransactionalBlock,
        SocialBlock,
        DescriptionBlock,
        DeliveryBlock,
        StarsBlock,
    ],
    Verbosity.LIST: [
        OpeningDayEvent,
        DescriptionEvent,
        OpeningHourBlock,
        Covid19Block,
        PhoneBlock,
        WebSiteBlock,
        ImagesBlock,
        GradesBlock,
        RecyclingBlock,
        TransactionalBlock,
        SocialBlock,
        DeliveryBlock,
        StarsBlock,
    ],
    Verbosity.SHORT: [OpeningHourBlock, Covid19Block],
}


def build_blocks(es_poi, lang, verbosity):
    """Returns the list of blocks we want
    depending on the verbosity.
    """
    blocks = []
    for c in BLOCKS_BY_VERBOSITY[verbosity]:
        if not c.is_enabled():
            continue
        block = c.from_es(es_poi, lang)
        if block is not None:
            blocks.append(block)
    return blocks
