from typing import Union

from .opening_hour import OpeningHourBlock
from .covid19 import Covid19Block
from .phone import PhoneBlock
from .information import InformationBlock
from .website import WebSiteBlock
from .contact import ContactBlock
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
from .environment import Weather
from .recycling import RecyclingBlock
from .transactional import TransactionalBlock
from .social import SocialBlock
from .description import DescriptionBlock
from .delivery import DeliveryBlock
from .stars import StarsBlock

AnyBlock = Union[
    OpeningHourBlock,
    Covid19Block,
    PhoneBlock,
    InformationBlock,
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
    Weather,
    RecyclingBlock,
    TransactionalBlock,
    SocialBlock,
    DescriptionBlock,
    DeliveryBlock,
    StarsBlock,
]
