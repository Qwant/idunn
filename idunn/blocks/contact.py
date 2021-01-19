from .base import BaseBlock
from typing import ClassVar, Literal


class ContactBlock(BaseBlock):
    type: Literal["contact"] = "contact"
    url: str

    @classmethod
    def from_es(cls, es_poi, lang):
        mail = es_poi.properties.get("email") or es_poi.properties.get("contact:email")
        if not mail:
            return None
        # TODO: maybe reuse pydantic for this check?
        if not isinstance(mail, str):
            return None

        return cls(url=f"mailto:{mail}")
