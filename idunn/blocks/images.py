import re
import logging
from urllib.parse import quote

import httpx
import requests
from pydantic import BaseModel, validator
from typing import List, Literal

from idunn import settings
from idunn.api.constants import PoiSource
from idunn.utils.thumbr import thumbr
from .base import BaseBlock
from ..datasources.mapillary import mapillary_client

logger = logging.getLogger(__name__)

# Resize images when using Thumbr, this is consistent with how the front
# displays them in the pannel and bigger than needed for the list view
IMAGES_HEIGHT = 165


class Image(BaseModel):
    url: str
    alt: str
    credits: str = ""
    source_url: str

    @validator("alt", pre=True)
    def validate_alt(cls, v):
        if not v:
            return ""
        return v


class ImagesBlock(BaseBlock):
    type: Literal["images"] = "images"
    images: List[Image]

    @classmethod
    def is_enabled(cls):
        return settings["BLOCK_IMAGES_ENABLED"]

    @staticmethod
    def get_source_url(raw_url):
        # Wikimedia commons media viewer when possible
        match = re.match(
            r"^https?://upload.wikimedia.org/wikipedia/commons/(?:.+/)?\w{1}/\w{2}/([^/]+)", raw_url
        )
        if match:
            commons_file_name = match.group(1)
            return (
                f"https://commons.wikimedia.org/wiki/File:{commons_file_name}"
                f"#/media/File:{commons_file_name}"
            )
        return raw_url

    @classmethod
    def build_image(cls, raw_url, **kwargs):
        if thumbr.is_enabled():
            thumb_url = thumbr.get_url_remote_thumbnail(raw_url, height=IMAGES_HEIGHT)
        else:
            thumb_url = raw_url
        return Image(url=thumb_url, **kwargs)

    @classmethod
    def get_pages_jaunes_images(cls, place, lang):
        source_url = None
        if "Links" in place:
            # Use pagesjaunes photos link when possible
            # (defined in legacy datafeed)
            source_url = place.get("Links", {}).get("viewPhotos")
        if not source_url:
            source_url = place.get_source_url() + "#ancrePhotoVideo"

        raw_urls = place.get_images_urls()
        place_name = place.get_name(lang)
        return [
            cls.build_image(raw_url, alt=place_name, source_url=source_url) for raw_url in raw_urls
        ]

    @classmethod
    def get_wikipedia_thumbnail(cls, place, lang):
        wiki_resp = place.get_wiki_resp(lang)
        if wiki_resp is None:
            return None
        raw_url = wiki_resp.get("pageimage_thumb")
        if not raw_url:
            return None
        if any(
            deny in raw_url
            for deny in (
                "street_enseigne",
                "location_map",
                "Open_Street_Map",
            )
        ):
            # Exclude irrelevant thumbnail
            return None
        return cls.build_image(
            raw_url, alt=wiki_resp.get("originalTitle", ""), source_url=cls.get_source_url(raw_url)
        )

    @classmethod
    def get_mapillary_image(cls, image_key):
        image_key = quote(image_key)
        thumb_1024_url, thumb_original_url = mapillary_client.fetch_mapillary_place(image_key)
        return cls.build_image(
            thumb_1024_url,
            source_url=thumb_original_url,
            alt="Mapillary",
            credits="From Mapillary, licensed under CC-BY-SA",
        )

    @classmethod
    def get_images(cls, place, lang):
        # Raw urls defined by the data source (Kuzzle, etc.)
        raw_urls = place.get_images_urls()
        if raw_urls:
            return [
                cls.build_image(raw_url, source_url=raw_url, alt=place.get_name(lang))
                for raw_url in raw_urls
            ]

        images = []

        # Tag "image"
        raw_url = place.properties.get("image") or ""
        is_wikipedia_image = "wikipedia.org" in raw_url
        if raw_url.startswith("http") and not is_wikipedia_image:
            # Image from "wikipedia.org" are ignored as the .jpg URL often points
            # to a HTML document, instead of a usable image.
            images.append(
                cls.build_image(
                    raw_url, source_url=cls.get_source_url(raw_url), alt=place.get_name(lang)
                )
            )
        else:
            # Thumbnail from Wikipedia extract as fallback
            wikipedia_thumb = cls.get_wikipedia_thumbnail(place, lang)
            if wikipedia_thumb:
                images.append(wikipedia_thumb)

        # Tag "mapillary"
        mapillary_image_key = place.properties.get("mapillary")
        if mapillary_image_key and settings["BLOCK_IMAGES_INCLUDE_MAPILLARY"]:
            images.append(cls.get_mapillary_image(mapillary_image_key))

        return images

    @classmethod
    def from_es(cls, place, lang):
        if place.get_source() == PoiSource.PAGESJAUNES:
            images = cls.get_pages_jaunes_images(place, lang)
        else:
            images = cls.get_images(place, lang)
        if not images:
            return None
        return cls(images=images)
