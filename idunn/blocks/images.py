import re
import logging
import hashlib
import posixpath
import urllib.parse
from urllib.parse import urlsplit, unquote

from apistar import types, validators
from .base import BaseBlock, BlocksValidator
from .wikipedia import WikidataConnector, WikiUndefinedException

logger = logging.getLogger(__name__)

class ThumbrHelper:

    def __init__(self):
        from app import settings
        self._sub_domains = settings.get('THUMBR_DOMAINS').split(',')
        self._use_thumbr = settings.get('THUMBR_ENABLED')
        self._salt = settings.get('THUMBR_SALT')

    def get_salt(self):
        return self._salt

    def use_thumbr(self):
        return self._use_thumbr

    def get_domain(self, hash):
        n = int(hash[0], 16) % (len(self._sub_domains))
        return 'https://' + self._sub_domains[n] + '/thumbr'

    def get_url_remote_thumbnail(self, source, width=0, height=0, bestFit=True, progressive=False, animated=False):
        displayErrorImage = False

        salt = self.get_salt()
        token = f"{source}{width}x{height}{salt}"
        hash = hashlib.sha256(bytes(token, encoding='utf8')).hexdigest()
        domain = self.get_domain(hash)

        size = int(width) * int(height)

        hashURLpart = f"{hash[0]}/{hash[1]}/{hash[2:]}"

        urlpath = urlsplit(source).path
        filename = posixpath.basename(unquote(urlpath))
        if not bool(re.match("^.*\.(jpg|jpeg|png|gif)$", filename)):
            filename += ".jpg"

        params = urllib.parse.urlencode({"u": urllib.parse.quote_plus(source), "q": 1 if displayErrorImage else 0, "b": 1 if bestFit else 0, "p": 1 if progressive else 0, "a": 1 if animated else 0})
        return domain + "/" + str(size) + "/" + hashURLpart + "/" + filename + "?" + params

class Image(types.Type):
    url = validators.String()
    alt = validators.String()
    credits = validators.String()

thumbr_helper = None

class ImagesBlock(BaseBlock):
    BLOCK_TYPE = "images"
    images = validators.Array(items=Image)

    @classmethod
    def from_es(cls, es_poi, lang):
        global thumbr_helper
        if es_poi.wiki_resp is not None:
            properties = es_poi.get('properties', {})
            place_name = properties.get('name')

            raw_url= es_poi.wiki_resp.get('pageimage_thumb')
            if raw_url is None:
                return None

            images = None
            if thumbr_helper is None:
                thumbr_helper = ThumbrHelper()
            if not thumbr_helper.use_thumbr():
                image_wiki = Image(url=urllib.parse.quote_plus(raw_url), alt=place_name, credits="wikimedia")
                images = [image_wiki]
            else:
                thumbr_url_large = thumbr_helper.get_url_remote_thumbnail(
                    source=raw_url,
                    width=30,
                    height=30
                )
                image_wiki_large = Image(url=thumbr_url_large, alt=place_name, credits="wikimedia")

                thumbr_url_small = thumbr_helper.get_url_remote_thumbnail(
                    source=raw_url,
                    width=15,
                    height=15
                )
                image_wiki_small = Image(url=thumbr_url_small, alt=place_name, credits="wikimedia")

                images = [image_wiki_large, image_wiki_small]

            if images is not None:
                return cls(images=images)
        return None
