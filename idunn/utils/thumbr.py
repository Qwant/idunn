import re
import logging
import hashlib
import posixpath
import urllib.parse
from urllib.parse import urlsplit, unquote

from idunn import settings

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

        if not bool(re.match(r"^.*\.(jpg|jpeg|png|gif|svg)$", filename, re.IGNORECASE)):
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


thumbr = ThumbrHelper()
