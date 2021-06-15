from .base import BaseBlock
from typing import Literal, Optional


class CommercialBlock(BaseBlock):
    type: Literal["commercial"] = "commercial"
    booking_url: Optional[str]
    appointment_url: Optional[str]
    order_url: Optional[str]

    @classmethod
    def from_es(cls, place, lang):
        args = {
            "booking_url": place.get_booking_url(),
            "appointment_url": place.get_appointment_url(),
            "order_url": place.get_appointment_url(),
        }

        if not any(args.values()):
            return None

        return cls(**args)
