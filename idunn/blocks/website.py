from .base import BaseBlock

from typing import Optional, Literal


class WebSiteBlock(BaseBlock):
    type: Literal["website"] = "website"
    url: str
    label: Optional[str]

    @classmethod
    def from_es(cls, place, lang):
        website = place.get_website()
        label = place.get_website_label()

        if not website:
            return None

        return cls(url=website, label=label)
