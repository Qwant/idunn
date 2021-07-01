from enum import Enum
from typing import List, Literal

from pydantic import BaseModel

from .base import BaseBlock


class Site(str, Enum):
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"


class Link(BaseModel):
    site: Site
    url: str


class SocialBlock(BaseBlock):
    type: Literal["social"] = "social"
    links: List[Link]

    @classmethod
    def from_es(cls, place, lang):
        links = [
            Link(site=site, url=url)
            for site, url in [
                (Site.FACEBOOK, place.get_facebook()),
                (Site.TWITTER, place.get_twitter()),
                (Site.INSTAGRAM, place.get_instagram()),
                (Site.YOUTUBE, place.get_youtube()),
            ]
            if url
        ]

        if not links:
            return None

        return cls(links=links)
