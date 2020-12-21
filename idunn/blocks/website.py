from .base import BaseBlock

from typing import ClassVar, Optional


class WebSiteBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "website"

    url: str
    label: Optional[str]

    @classmethod
    def from_es(cls, es_poi, lang):
        website = es_poi.get_website()
        label = es_poi.get_website_label()

        if not website:
            return None

        return cls(url=website, label=label)
