from apistar import types, validators

from .base import BaseBlock
from ..api import utils


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
        parsed_phone_number = utils.parse_phone_number(raw)
        if parsed_phone_number is None:
            return None
        # At this point, it should all work but just in case...
        e164 = utils.get_e164_phone_number(parsed_phone_number)
        national = utils.get_national_phone_number(parsed_phone_number)
        international = utils.get_international_phone_number(parsed_phone_number)
        if e164 is None or national is None or international is None:
            return None
        return cls(
            url='tel:{}'.format(e164),
            international_format=international,
            local_format=national
        )
