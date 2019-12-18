from enum import Enum
import logging
from datetime import datetime, timedelta, date
from pytz import timezone, UTC
from tzwhere import tzwhere
import humanized_opening_hours as hoh
from humanized_opening_hours.exceptions import HOHError
from pydantic import BaseModel, conint, constr
from typing import ClassVar, List, Optional

from .base import BaseBlock
from .opening_hour import get_tz, get_coord, tz, parse_time_block, get_days, OpeningHoursType


logger = logging.getLogger(__name__)


class YesNoAnswer(str, Enum):
    yes = 'yes'
    no = 'no'


class DaysType(BaseModel):
    dayofweek: conint(ge=1, le=7)
    local_date: date
    status: YesNoAnswer
    happy_hours: List[OpeningHoursType]


class HappyHourBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = 'happy_hours'
    STATUSES: ClassVar = ['yes', 'no']

    status: YesNoAnswer # bound to STATUSES
    next_transition_datetime: Optional[str]
    seconds_before_next_transition: Optional[int]
    raw: str
    days: List[DaysType]

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
