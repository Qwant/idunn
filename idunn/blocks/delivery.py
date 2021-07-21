from enum import Enum
from typing import List, Literal

from .base import BaseBlock


class DeliveryType(Enum):
    CLICK_AND_COLLECT = "click_and_collect"
    DELIVERY = "delivery"
    TAKEAWAY = "takeaway"


class DeliveryBlock(BaseBlock):
    type: Literal["delivery"] = "delivery"
    available: List[DeliveryType]

    @classmethod
    def from_es(cls, place, lang):
        available = [
            delivery_type
            for delivery_type, is_available in [
                (DeliveryType.CLICK_AND_COLLECT, place.has_click_and_collect()),
                (DeliveryType.DELIVERY, place.has_delivery()),
                (DeliveryType.TAKEAWAY, place.has_takeaway()),
            ]
            if is_available
        ]

        if not available:
            return None

        return cls(available=available)
