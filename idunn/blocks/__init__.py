from typing import Union

from .opening_hour import OpeningHourBlock
from .phone import PhoneBlock
from .information import InformationBlock
from .reviews import ReviewsBlock
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
from .transactional import TransactionalBlock
from .social import SocialBlock
from .description import DescriptionBlock
from .delivery import DeliveryBlock
from .stars import StarsBlock

AnyBlock = Union[
    OpeningHourBlock,
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
    TransactionalBlock,
    SocialBlock,
    DescriptionBlock,
    DeliveryBlock,
    StarsBlock,
    ReviewsBlock,
]
