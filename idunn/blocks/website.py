import logging
import requests
from requests.exceptions import HTTPError, RequestException, Timeout
from apistar import validators

from .base import BaseBlock, BlocksValidator

class WebSiteBlock(BaseBlock):
    BLOCK_TYPE = "website"

    url = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang):
        website = es_poi.get('properties', {}).get('contact:website') or es_poi.get('properties', {}).get('website')
        if website is None:
            return None

        return cls(
            url=website
        )
