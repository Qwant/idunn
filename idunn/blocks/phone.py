from apistar import types, validators

from .base import BaseBlock


class PhoneBlock(BaseBlock):
    BLOCK_TYPE = 'phone'

    url = validators.String()
    international_format = validators.String()
    local_format = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang):
        raw = es_poi.get_phone()
        if not raw:
            return None

        return cls(
            url=f'tel:{raw}',
            international_format=raw,
            local_format=raw
        )
