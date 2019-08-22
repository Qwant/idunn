import logging
from datetime import datetime, timedelta, date
from pytz import timezone, UTC
from apistar import validators, types
from tzwhere import tzwhere
import humanized_opening_hours as hoh
from humanized_opening_hours.exceptions import HOHError

from .base import BaseBlock
from .opening_hour import get_tz, get_coord, tz, parse_time_block, get_days, OpeningHoursType


logger = logging.getLogger(__name__)


class DaysType(types.Type):
    dayofweek = validators.Integer(minimum=1, maximum=7)
    local_date = validators.Date()
    status = validators.String(enum=['yes', 'no'])
    happy_hours = validators.Array(items=OpeningHoursType)


class HappyHourBlock(BaseBlock):
    BLOCK_TYPE = 'happy_hours'
    STATUSES = ['yes', 'no']

    status = validators.String(enum=STATUSES)
    next_transition_datetime = validators.String(allow_null=True)
    seconds_before_next_transition = validators.Integer(allow_null=True)
    raw = validators.String()
    days = validators.Array(items=DaysType)

    @classmethod
    def init_class(cls, status, next_transition_datetime, time_before_next, oh, poi_dt, raw):
        return cls(
            status=status,
            next_transition_datetime=next_transition_datetime,
            seconds_before_next_transition=time_before_next,
            raw=oh.field,
            days=get_days(cls, oh, poi_dt)
        )

    @classmethod
    def from_es(cls, es_poi, lang):
        return parse_time_block(cls, es_poi, lang, es_poi.get_raw_happy_hours())
