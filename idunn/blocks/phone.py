from apistar import types, validators

from .base import BaseBlock


class PhoneBlock(BaseBlock):
    BLOCK_TYPE = 'phone'

    url = validators.String()
    international_format = validators.String()
    local_format = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang, prom):
        raw = es_poi.get('properties', {}).get('phone') or es_poi.get('properties', {}).get('contact:phone')
        if raw is None:
            return None

        return cls(
            url=f'tel:{raw}',
            international_format=raw,
            local_format=raw
        )
