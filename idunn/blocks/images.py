import re
import logging
import hashlib
import posixpath
import urllib.parse
from urllib.parse import urlsplit, unquote, quote
from pydantic import BaseModel, validator
from typing import List, Literal

from idunn import settings
from idunn.api.constants import PoiSource
from .base import BaseBlock


logger = logging.getLogger(__name__)


class ThumbrHelper:
    def __init__(self):
        self._thumbr_urls = settings.get("THUMBR_URLS").split(",")
        self._thumbr_enabled = settings.get("THUMBR_ENABLED")
        self._salt = settings.get("THUMBR_SALT") or ""
        if self._thumbr_enabled and not self._salt:
            logger.warning("Thumbr salt is empty")

    def get_salt(self):
        return self._salt

    def is_enabled(self):
        return bool(self._thumbr_enabled)

    def get_thumbr_url(self, img_hash):
        n = int(img_hash[0], 16) % (len(self._thumbr_urls))
        return self._thumbr_urls[n]

    def get_url_remote_thumbnail(
        self,
        source,
        width=0,
        height=0,
        bestFit=True,
        progressive=False,
        animated=False,
        displayErrorImage=False,
    ):
        size = f"{width}x{height}"
        token = f"{source}{size}{self.get_salt()}"
        img_hash = hashlib.sha256(bytes(token, encoding="utf8")).hexdigest()
        base_url = self.get_thumbr_url(img_hash)

        hashURLpart = f"{img_hash[0]}/{img_hash[1]}/{img_hash[2:]}"
        filename = posixpath.basename(unquote(urlsplit(source).path))

        if not bool(re.match(r"^.*\.(jpg|jpeg|png|gif)$", filename, re.IGNORECASE)):
            filename += ".jpg"

        params = urllib.parse.urlencode(
            {
                "u": source,
                "q": 1 if displayErrorImage else 0,
                "b": 1 if bestFit else 0,
                "p": 1 if progressive else 0,
                "a": 1 if animated else 0,
            }
        )
        return base_url + "/" + size + "/" + hashURLpart + "/" + filename + "?" + params


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
    _thumb_helper = None

    @classmethod
    def is_enabled(cls):
        return settings["BLOCK_IMAGES_ENABLED"]

    @classmethod
    def get_thumbr_helper(cls):
        if cls._thumb_helper is None:
            cls._thumb_helper = ThumbrHelper()
        return cls._thumb_helper

    @staticmethod
    def get_source_url(raw_url):
        # Wikimedia commons media viewer when possible
        match = re.match(
            r"^https?://upload.wikimedia.org/wikipedia/commons/(?:.+/)?\w{1}/\w{2}/([^/]+)", raw_url
        )
        if match:
            commons_file_name = match.group(1)
            return f"https://commons.wikimedia.org/wiki/File:{commons_file_name}" \
                   f"#/media/File:{commons_file_name}"
        return raw_url

    @classmethod
    def build_image(cls, raw_url, **kwargs):
        thumbr = cls.get_thumbr_helper()
        if thumbr.is_enabled():
            thumb_url = thumbr.get_url_remote_thumbnail(raw_url)
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
        image_url = f"https://images.mapillary.com/{image_key}/thumb-1024.jpg"
        source_url = f"https://www.mapillary.com/app/?focus=photo&pKey={image_key}"
        return cls.build_image(
            image_url,
            source_url=source_url,
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
