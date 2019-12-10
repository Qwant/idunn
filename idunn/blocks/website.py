from .base import BaseBlock

from typing import ClassVar


class WebSiteBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "website"

    url: str

    @classmethod
    def from_es(cls, es_poi, lang):
        website = es_poi.get_website()
        if not website:
            return None
        return cls(
            url=website
        )
