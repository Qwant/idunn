from apistar import validators
from .base import BaseBlock


class WebSiteBlock(BaseBlock):
    BLOCK_TYPE = "website"

    url = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang):
        website = es_poi.get_website()
        if not website:
            return None
        return cls(
            url=website
        )
