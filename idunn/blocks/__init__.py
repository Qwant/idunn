from .opening_hour import OpeningHourBlock
from .happy_hour import HappyHourBlock
from .phone import PhoneBlock
from .information import InformationBlock
from .website import WebSiteBlock
from .contact import ContactBlock
from .wikipedia import (
    WikipediaBlock,
    WikiUndefinedException,
    GET_WIKI_INFO,
    WikipediaCache,
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

ALL_BLOCKS = [
    OpeningHourBlock,
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
]
BLOCK_TYPE_TO_CLASS = {b.BLOCK_TYPE: b for b in ALL_BLOCKS}
