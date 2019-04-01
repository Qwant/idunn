import re
import logging
import hashlib
import posixpath
import urllib.parse
from urllib.parse import urlsplit, unquote

from apistar import types, validators
from .base import BaseBlock

logger = logging.getLogger(__name__)

class ThumbrHelper:
    def __init__(self):
        from app import settings
        self._sub_domains = settings.get('THUMBR_DOMAINS').split(',')
        self._thumbr_enabled = settings.get('THUMBR_ENABLED')
        self._salt = settings.get('THUMBR_SALT')

    def get_salt(self):
        return self._salt

    def is_enabled(self):
        return bool(self._thumbr_enabled)

    def get_domain(self, hash):
        n = int(hash[0], 16) % (len(self._sub_domains))
        return 'https://' + self._sub_domains[n] + '/thumbr'

    def get_url_remote_thumbnail(self, source, width=0, height=0, bestFit=True, progressive=False, animated=False):
        displayErrorImage = False

        salt = self.get_salt()
        token = f"{source}{width}x{height}{salt}"
        hash = hashlib.sha256(bytes(token, encoding='utf8')).hexdigest()
        domain = self.get_domain(hash)

        size = f"{width}x{height}"

        hashURLpart = f"{hash[0]}/{hash[1]}/{hash[2:]}"

        urlpath = urlsplit(source).path
        filename = posixpath.basename(unquote(urlpath))
        if not bool(re.match("^.*\.(jpg|jpeg|png|gif)$", filename, re.IGNORECASE)):
            filename += ".jpg"

        params = urllib.parse.urlencode({
            "u": source,
            "q": 1 if displayErrorImage else 0,
            "b": 1 if bestFit else 0,
            "p": 1 if progressive else 0,
            "a": 1 if animated else 0
        })
        return domain + "/" + size + "/" + hashURLpart + "/" + filename + "?" + params


class Image(types.Type):
    url = validators.String()
    alt = validators.String()
    credits = validators.String(default="")
    source_url = validators.String()

class ImagesBlock(BaseBlock):
    BLOCK_TYPE = "images"
    images = validators.Array(items=Image)

    _thumb_helper = None

    @classmethod
    def get_thumbr_helper(cls):
        if cls._thumb_helper is None:
            cls._thumb_helper = ThumbrHelper()
        return cls._thumb_helper

    @staticmethod
    def get_source_url(raw_url):
        # Use wikimedia commons media viewer when possible
        match = re.match(
            r'^https://upload.wikimedia.org/wikipedia/commons/(?:.+/)?\w{1}/\w{2}/([^/]+)',
            raw_url
        )
        if match:
            commons_file_name = match.group(1)
            return 'https://commons.wikimedia.org/wiki/File:{0}#/media/File:{0}'.format(commons_file_name)
        return raw_url

    @classmethod
    def from_es(cls, es_poi, lang):
        wiki_resp = es_poi.get_wiki_resp(lang)
        if wiki_resp is None:
            return None

        place_name = es_poi.get_name(lang)
        raw_url = wiki_resp.get('pageimage_thumb')
        if raw_url is None:
            return None

        source_url = cls.get_source_url(raw_url)
        thumbr = cls.get_thumbr_helper()
        if thumbr.is_enabled():
            thumbr = cls.get_thumbr_helper()
            thumb_url = thumbr.get_url_remote_thumbnail(raw_url)
        else:
            thumb_url = raw_url

        image_wiki = Image(
            url=thumb_url,
            alt=place_name,
            source_url=source_url
        )
        return cls(images=[image_wiki])
