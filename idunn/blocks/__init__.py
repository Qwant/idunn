from typing import Union

from .opening_hour import OpeningHourBlock
from .covid19 import Covid19Block
from .phone import PhoneBlock
from .information import InformationBlock
from .website import WebSiteBlock
from .contact import ContactBlock
from .wikipedia import WikipediaBlock
from .images import ImagesBlock
from .services_and_information import (
    ServicesAndInformationBlock,
    AccessibilityBlock,
    InternetAccessBlock,
    BreweryBlock,
    CuisineBlock,
)
from .grades import GradesBlock
from .events import OpeningDayEvent, DescriptionEvent
from .environment import AirQuality, Weather
from .recycling import RecyclingBlock
from .transactional import TransactionalBlock
from .social import SocialBlock
from .description import DescriptionBlock

AnyBlock = Union[
    OpeningHourBlock,
    Covid19Block,
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
    RecyclingBlock,
    TransactionalBlock,
    SocialBlock,
    DescriptionBlock,
]
