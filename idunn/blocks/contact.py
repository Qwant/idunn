from .base import BaseBlock
from typing import Literal


class ContactBlock(BaseBlock):
    type: Literal["contact"] = "contact"
    url: str

    @classmethod
    def from_es(cls, es_poi, lang):
        mail = es_poi.properties.get("email") or es_poi.properties.get("contact:email")

        if not mail or not isinstance(mail, str):
            return None

        return cls(url=f"mailto:{mail}")
