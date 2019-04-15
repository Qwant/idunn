from apistar import validators

from .base import BaseBlock

class ContactBlock(BaseBlock):
    BLOCK_TYPE = "contact"

    url = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang):
        mail = es_poi.properties.get('email') or es_poi.properties.get('contact:email')
        if not mail:
            return None

        return cls(
            url=f'mailto:{mail}'
        )
