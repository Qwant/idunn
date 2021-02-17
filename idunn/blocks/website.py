from urllib.parse import urlparse
from typing import Literal

from .base import BaseBlock


class WebSiteBlock(BaseBlock):
    type: Literal["website"] = "website"
    url: str
    label: str

    @classmethod
    def from_es(cls, place, lang):
        website = place.get_website()
        label = place.get_website_label()

        if not website:
            return None

        if not label:
            # Extract domain name or hostname from website
            label = urlparse(website).netloc

        return cls(url=website, label=label)
