import logging
from datetime import datetime, timedelta, date
from pytz import timezone, UTC
from tzwhere import tzwhere
import humanized_opening_hours as hoh
from humanized_opening_hours.exceptions import HOHError
from lark.exceptions import LarkError
from pydantic import BaseModel, conint, constr
from typing import ClassVar, List, Optional

from .base import BaseBlock


logger = logging.getLogger(__name__)

"""
We load the tz structure once when Idunn starts since it's a time consuming step
"""
tz = tzwhere.tzwhere(forceTZ=True)


def get_tz(poi_tzname, lat, lon):
    """
    Returns the timezone corresponding to the coordinates of the POI.
    """
    if lon is not None and lat is not None:
        return timezone(poi_tzname)
    return None


def get_coord(es_poi):
    """
    Returns the coordinates from the POI json
    """
    coord = es_poi.get_coord()
    if coord:
        lon = coord.get('lon')
        lat = coord.get('lat')
        return (lat, lon)
    return None


class OpeningHoursType(BaseModel):
    beginning: str
    end: str


class DaysType(BaseModel):
    dayofweek: conint(ge=1, le=7)
    local_date: date
    status: constr(regex='(open|closed)')
    opening_hours: List[OpeningHoursType]


def parse_time_block(cls, es_poi, lang, raw):
    if not raw:
        return None

    poi_coord = get_coord(es_poi)
    poi_lat = poi_coord[0]
    poi_lon = poi_coord[1]

    poi_tzname = tz.tzNameAt(poi_lat, poi_lon, forceTZ=True)
    poi_tz = get_tz(poi_tzname, poi_lat, poi_lon)

    if poi_tz is None:
        logger.info("No timezone found for poi %s", es_poi.get('id'))
        return None

    hoh_args = {}
    if any(k in raw for k in ['sunset', 'sunrise', 'dawn', 'dusk']):
        # Optimization: use astral location only when necessary
        hoh_args['location'] = (poi_lat, poi_lon, poi_tzname, 24)
    try:
        oh = hoh.OHParser(raw, **hoh_args)
    except (HOHError, LarkError):
        logger.info(
            "Failed to parse happy_hours field, id:'%s' raw:'%s'",
            es_poi.get_id(), raw, exc_info=True
        )
        return None

    poi_dt = UTC.localize(datetime.utcnow()).astimezone(poi_tz)

    if oh.is_open(poi_dt.replace(tzinfo=None)):
        status = cls.STATUSES[0]
    else:
        status = cls.STATUSES[1]

    if cls.BLOCK_TYPE == OpeningHourBlock.BLOCK_TYPE and (raw == '24/7' or oh.is_24_7):
        return cls.init_class(status, None, None, oh, poi_dt, raw)

    # The current version of the hoh lib doesn't allow to use the next_change() function
    # with an offset aware datetime.
    # This is why we replace the timezone info until this problem is fixed in the library.
    try:
        nt = oh.next_change(dt=poi_dt.replace(tzinfo=None))
    except HOHError:
        logger.info("HOHError: Failed to compute next transition for poi %s", es_poi.get('id'), exc_info=True)
        return None

    # Then we localize the next_change transition datetime in the local POI timezone.
    next_transition = poi_tz.localize(nt.replace(tzinfo=None))
    next_transition = round_dt_to_minute(next_transition)

    next_transition_datetime = next_transition.isoformat()
    delta = next_transition - poi_dt
    time_before_next = int(delta.total_seconds())

    return cls.init_class(status, next_transition_datetime, time_before_next, oh, poi_dt, raw)


def round_dt_to_minute(dt):
    dt += timedelta(seconds=30)
    return dt.replace(second=0, microsecond=0)


def round_time_to_minute(t):
    dt = datetime.combine(date(2000,1,1), t)
    rounded = round_dt_to_minute(dt)
    return rounded.time()


def get_days(cls, oh_parser, dt):
    last_monday = dt.date() - timedelta(days=dt.weekday())
    days = []
    for x in range(0,7):
        day = last_monday + timedelta(days=x)
        oh_day = oh_parser.get_day(day)
        periods = oh_day.opening_periods()
        day_value = {
            'dayofweek': day.isoweekday(),
            'local_date': day.isoformat(),
            'status': cls.STATUSES[0] if len(periods) > 0 else cls.STATUSES[1],
            cls.BLOCK_TYPE: []
        }
        for beginning_dt, end_dt in periods:
            if beginning_dt.date() < day:
                continue
            beginning = round_time_to_minute(beginning_dt.time())
            end = round_time_to_minute(end_dt.time())
            day_value[cls.BLOCK_TYPE].append(
                {
                    'beginning': beginning.strftime('%H:%M'),
                    'end': end.strftime('%H:%M')
                }
            )
        days.append(day_value)
    return days


class OpeningHourBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = 'opening_hours'
    STATUSES: ClassVar = ['open', 'closed']

    status: constr(regex='({})'.format('|'.join(STATUSES)))
    next_transition_datetime: Optional[str]
    seconds_before_next_transition: Optional[int]
    is_24_7: bool
    raw: str
    days: List[DaysType]

    @classmethod
    def init_class(cls, status, next_transition_datetime, time_before_next, oh, poi_dt, raw):
        if raw == '24/7' or oh.is_24_7:
            return cls(
                status=status,
                next_transition_datetime=None,
                seconds_before_next_transition=None,
                is_24_7=True,
                raw=oh.field,
                days=get_days(cls, oh, poi_dt)
            )

        if all(r.status == 'closed' for r in oh.rules):
            # Ignore opening_hours such as "Apr 1-Sep 30: off", causing overflow
            return None

        return cls(
            status=status,
            next_transition_datetime=next_transition_datetime,
            seconds_before_next_transition=time_before_next,
            is_24_7=oh.is_24_7,
            raw=oh.field,
            days=get_days(cls, oh, poi_dt)
        )

    @classmethod
    def from_es(cls, es_poi, lang):
        return parse_time_block(cls, es_poi, lang, es_poi.get_raw_opening_hours())
