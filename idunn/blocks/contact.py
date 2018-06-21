import logging
import requests
from requests.exceptions import HTTPError, RequestException, Timeout
from apistar import validators

from .base import BaseBlock, BlocksValidator

class ContactBlock(BaseBlock):
    BLOCK_TYPE = "contact"

    url = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang):
        mail = es_poi.get('properties', {}).get('email') or es_poi.get('properties', {}).get('contact:email')
        if mail is None:
            return None

        return cls(
            url=f'mailto:{mail}'
        )
