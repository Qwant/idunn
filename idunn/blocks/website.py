import logging
from urllib.parse import urlparse
from typing import Literal
from pydantic import ValidationError, AnyHttpUrl

from .base import BaseBlock

logger = logging.getLogger(__name__)


class WebSiteBlock(BaseBlock):
    type: Literal["website"] = "website"
    url: AnyHttpUrl
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

        try:
            return cls(url=website, label=label)
        except ValidationError:
            logger.debug(
                "Website block is invalid for %s. Website: %s",
                place.get_id(),
                website,
                exc_info=True,
            )
            return None
