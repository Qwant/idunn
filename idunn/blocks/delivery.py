from enum import Enum
from typing import Literal

from .base import BaseBlock


class DeliveryState(Enum):
    YES = "yes"
    UNKNOWN = "unknown"

    @classmethod
    def from_bool(cls, is_yes: bool):
        return cls.YES if is_yes else cls.UNKNOWN


class DeliveryBlock(BaseBlock):
    type: Literal["delivery"] = "delivery"
    click_and_collect: DeliveryState
    delivery: DeliveryState
    takeaway: DeliveryState

    @classmethod
    def from_es(cls, place, lang):
        states = {
            "click_and_collect": DeliveryState.from_bool(place.has_click_and_collect()),
            "delivery": DeliveryState.from_bool(place.has_delivery()),
            "takeaway": DeliveryState.from_bool(place.has_takeaway()),
        }

        if all(state == DeliveryState.UNKNOWN for state in states.values()):
            return None

        return cls(**states)
