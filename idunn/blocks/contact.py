from .base import BaseBlock
from typing import Literal


class ContactBlock(BaseBlock):
    type: Literal["contact"] = "contact"
    url: str
    email: str

    @classmethod
    def from_es(cls, place, lang):
        mail = place.properties.get("email") or place.properties.get("contact:email")

        if not mail or not isinstance(mail, str):
            return None

        return cls(url=f"mailto:{mail}", email=mail)
