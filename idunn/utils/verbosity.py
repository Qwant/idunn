from enum import Enum

from idunn.blocks import (
    Weather,
    ContactBlock,
    DescriptionEvent,
    GradesBlock,
    ReviewsBlock,
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
        ReviewsBlock,
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
        ReviewsBlock,
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
