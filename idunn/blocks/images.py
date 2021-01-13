import re
import logging
import hashlib
import posixpath
import urllib.parse
from urllib.parse import urlsplit, unquote
from pydantic import BaseModel, validator
from typing import ClassVar, List, Literal

from idunn import settings
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

    def get_thumbr_url(self, hash):
        n = int(hash[0], 16) % (len(self._thumbr_urls))
        return self._thumbr_urls[n]

    def get_url_remote_thumbnail(
        self, source, width=0, height=0, bestFit=True, progressive=False, animated=False
    ):
        displayErrorImage = False

        salt = self.get_salt()
        token = f"{source}{width}x{height}{salt}"
        hash = hashlib.sha256(bytes(token, encoding="utf8")).hexdigest()
        base_url = self.get_thumbr_url(hash)

        size = f"{width}x{height}"
        hashURLpart = f"{hash[0]}/{hash[1]}/{hash[2:]}"

        url_path = urlsplit(source).path
        filename = posixpath.basename(unquote(url_path))
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
        from app import settings

        return settings["BLOCK_IMAGES_ENABLED"]

    @classmethod
    def get_thumbr_helper(cls):
        if cls._thumb_helper is None:
            cls._thumb_helper = ThumbrHelper()
        return cls._thumb_helper

    @staticmethod
    def get_source_url(raw_url, place):
        if "Links" in place:
            # Use pagesjaunes photos link when possible
            link = place.get("Links", {}).get("viewPhotos")
            if link:
                return link

        # Use wikimedia commons media viewer when possible
        match = re.match(
            r"^https://upload.wikimedia.org/wikipedia/commons/(?:.+/)?\w{1}/\w{2}/([^/]+)", raw_url
        )
        if match:
            commons_file_name = match.group(1)
            return "https://commons.wikimedia.org/wiki/File:{0}#/media/File:{0}".format(
                commons_file_name
            )
        return raw_url

    @classmethod
    def from_es(cls, es_poi, lang):
        raw_urls = es_poi.get_images_urls()
        if not raw_urls:
            # Fallback to wikipedia image
            wiki_resp = es_poi.get_wiki_resp(lang)
            if wiki_resp is not None:
                raw_url = wiki_resp.get("pageimage_thumb")
                if raw_url:
                    raw_urls.append(raw_url)

        if not raw_urls:
            return None

        place_name = es_poi.get_name(lang)
        images = []
        for raw_url in raw_urls:
            source_url = cls.get_source_url(raw_url, place=es_poi)
            thumbr = cls.get_thumbr_helper()
            if thumbr.is_enabled():
                thumbr = cls.get_thumbr_helper()
                thumb_url = thumbr.get_url_remote_thumbnail(raw_url)
            else:
                thumb_url = raw_url

            images.append(Image(url=thumb_url, alt=place_name, source_url=source_url))

        return cls(images=images)
