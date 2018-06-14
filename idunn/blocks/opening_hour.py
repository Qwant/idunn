from apistar import validators

from .base import BaseBlock


class OpeningHourBlock(BaseBlock):
    BLOCK_TYPE = 'opening_hours'

    status = validators.String()
    next_transition_time = validators.String()
    seconds_before_next_transition = validators.Integer()
    is_24_7 = validators.Boolean()
    raw = validators.String()
    days = validators.Array()

    @classmethod
    def from_es(cls, es_poi, lang):
        raw = es_poi.get('properties', {}).get('opening_hours')
        if raw is None:
            return None
        is247 = raw == '24/7'

        return cls(
            status='',
            next_transition_time='',
            seconds_before_next_transition=0,
            is_24_7=is247,
            raw=raw,
            days=[]
        )
