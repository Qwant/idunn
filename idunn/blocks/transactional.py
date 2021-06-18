from .base import BaseBlock
from typing import Literal, Optional


class TransactionalBlock(BaseBlock):
    type: Literal["transactional"] = "transactional"
    booking_url: Optional[str]
    appointment_url: Optional[str]
    quotation_request_url: Optional[str]

    @classmethod
    def from_es(cls, place, lang):
        args = {
            "booking_url": place.get_booking_url(),
            "appointment_url": place.get_appointment_url(),
            "quotation_request_url": place.get_quotation_request_url(),
        }

        if not any(args.values()):
            return None

        return cls(**args)
