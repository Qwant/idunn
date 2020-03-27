from .opening_hour import OpeningHourBlock
from .covid19 import Covid19Block
from .happy_hour import HappyHourBlock
from .phone import PhoneBlock
from .information import InformationBlock
from .website import WebSiteBlock
from .contact import ContactBlock
from .wikipedia import (
    WikipediaBlock,
    WikiUndefinedException,
    GET_WIKI_INFO,
)
from .images import ImagesBlock
from .services_and_information import (
    ServicesAndInformationBlock,
    AccessibilityBlock,
    InternetAccessBlock,
    BreweryBlock,
    CuisineBlock,
)
from .grades import GradesBlock
from .events import (
    OpeningDayEvent,
    DescriptionEvent,
)
from .environment import (
    AirQuality,
    Weather,
)


ALL_BLOCKS = [
    OpeningHourBlock,
    Covid19Block,
    HappyHourBlock,
    PhoneBlock,
    InformationBlock,
    WikipediaBlock,
    WebSiteBlock,
    ContactBlock,
    ServicesAndInformationBlock,
    AccessibilityBlock,
    InternetAccessBlock,
    BreweryBlock,
    ImagesBlock,
    GradesBlock,
    OpeningDayEvent,
    DescriptionEvent,
    CuisineBlock,
    AirQuality,
    Weather,
]

BLOCK_TYPE_TO_CLASS = {b.BLOCK_TYPE: b for b in ALL_BLOCKS}
