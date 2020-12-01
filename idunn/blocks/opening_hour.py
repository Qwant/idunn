import logging
from datetime import datetime, timedelta, date
from pytz import timezone, utc
from tzwhere import tzwhere
from pydantic import BaseModel, conint, constr
from typing import List, Literal, Optional

from .base import BaseBlock
from idunn.utils.opening_hours import OpeningHours

OPEN = "open"
CLOSED = "closed"


logger = logging.getLogger(__name__)

# We load the tz structure once when Idunn starts since it's a time consuming step
tz = tzwhere.tzwhere(forceTZ=True)


def get_tz(poi_tzname, lat, lon):
    """
    Returns the timezone corresponding to the coordinates of the POI.
    """
    if lon is not None and lat is not None:
        return timezone(poi_tzname)
    return None


def get_coord(place):
    """
    Returns the coordinates from the POI json
    """
    coord = place.get_coord()
    if coord:
        lon = coord.get("lon")
        lat = coord.get("lat")
        return (lat, lon)
    return None


class OpeningHoursType(BaseModel):
    beginning: str
    end: str


class DaysType(BaseModel):
    dayofweek: conint(ge=1, le=7)
    local_date: str  # should be date but for some reason, fastapi jsonable_encoder just don't care
    status: constr(regex="(open|closed)")
    opening_hours: List[OpeningHoursType]


def parse_time_block(cls, es_poi, lang, raw):
    if not raw:
        return None

    # Fallback to London coordinates if POI coordinates are not known.
    poi_lat, poi_lon = get_coord(es_poi) or (51.5, 0)
    poi_country_code = es_poi.get_country_code()

    poi_tzname = tz.tzNameAt(poi_lat, poi_lon, forceTZ=True)
    poi_tz = get_tz(poi_tzname, poi_lat, poi_lon)

    if poi_tz is None:
        logger.info("No timezone found for poi %s", es_poi.get("id"))
        return None

    try:
        oh = OpeningHours(raw, poi_tz, poi_country_code)
    except SyntaxError:
        logger.info(
            "Failed to validate opening_hours field, id:'%s' raw:'%s'",
            es_poi.get_id(),
            raw,
            exc_info=True,
        )
        return None

    curr_dt = utc.localize(datetime.utcnow())

    if oh.is_open(curr_dt):
        status = cls.STATUSES[0]
    else:
        status = cls.STATUSES[1]

    if cls.BLOCK_TYPE == OpeningHourBlock.BLOCK_TYPE and oh.is_24_7(curr_dt):
        return cls.init_class(status, None, None, oh, curr_dt, raw)

    next_transition = oh.next_change(curr_dt)

    if next_transition is None:
        return None

    # Then we localize the next_change transition datetime in the local POI timezone.
    next_transition = round_dt_to_minute(next_transition)
    delta = next_transition - curr_dt
    time_before_next = int(delta.total_seconds())

    return cls.init_class(status, next_transition.isoformat(), time_before_next, oh, curr_dt, raw)


def round_dt_to_minute(dt):
    dt += timedelta(seconds=30)
    return dt.replace(second=0, microsecond=0)


def round_time_to_minute(t):
    dt = datetime.combine(date(2000, 1, 1), t)
    rounded = round_dt_to_minute(dt)
    return rounded.time()


def get_days(oh, dt):
    last_monday = dt.date() - timedelta(days=dt.weekday())
    days = []

    for x in range(0, 7):
        day = last_monday + timedelta(days=x)
        intervals = oh.get_open_intervals_at_date(day, overlap_next_day=True)
        days.append(
            {
                "dayofweek": day.isoweekday(),
                "local_date": day.isoformat(),
                "status": OPEN if len(intervals) > 0 else CLOSED,
                "opening_hours": [
                    {"beginning": start.strftime("%H:%M"), "end": end.strftime("%H:%M")}
                    for start, end,  _comment in intervals
                ],
            }
        )

    return days


class OpeningHourBlock(BaseBlock):
    type: Literal["opening_hours"] = "opening_hours"
    status: constr(regex="(open|closed)")
    next_transition_datetime: Optional[str]
    seconds_before_next_transition: Optional[int]
    is_24_7: bool
    raw: str
    days: List[DaysType]

    @classmethod
    def init_class(cls, status, next_transition_datetime, time_before_next, oh, curr_dt, raw):
        is_24_7 = status == OPEN and next_transition_datetime is None
        return cls(
            status=status,
            next_transition_datetime=next_transition_datetime if not is_24_7 else None,
            seconds_before_next_transition=time_before_next if not is_24_7 else None,
            is_24_7=is_24_7,
            raw=raw,
            days=get_days(oh, curr_dt),
        )

    @staticmethod
    def get_raw_oh(place):
        return place.get_raw_opening_hours()

    @classmethod
    def from_es_with_oh(cls, place, _lang, raw_oh):
        # Fallback to London coordinates if POI coordinates are not known.
        poi_lat, poi_lon = get_coord(place) or (51.5, 0)
        poi_country_code = place.get_country_code()

        poi_tzname = tz.tzNameAt(poi_lat, poi_lon, forceTZ=True)
        poi_tz = get_tz(poi_tzname, poi_lat, poi_lon)

        if poi_tz is None:
            logger.info("No timezone found for poi %s", place.get("id"))
            return None

        oh = OpeningHours(raw_oh, poi_tz, poi_country_code)
        curr_dt = utc.localize(datetime.utcnow())

        if not oh.validate():
            logger.info(
                "Failed to validate opening_hours field, id:'%s' raw:'%s'",
                place.get_id(),
                raw_oh,
                exc_info=True,
            )
            return None

        next_transition = oh.next_change(curr_dt)

        if oh.is_open(curr_dt):
            status = OPEN
            if next_transition is None:
                # open 24/7
                return cls.init_class(status, None, None, oh, curr_dt, raw_oh)
        else:
            status = CLOSED
            if next_transition is None:
                return None

        # Then we localize the next_change transition datetime in the local POI timezone.
        next_transition = round_dt_to_minute(next_transition)
        delta = next_transition - curr_dt
        time_before_next = int(delta.total_seconds())

        return cls.init_class(
            status, next_transition.isoformat(), time_before_next, oh, curr_dt, raw_oh
        )

    @classmethod
    def from_es(cls, place, lang):
        raw_oh = cls.get_raw_oh(place)

        if raw_oh is None:
            return None

        return cls.from_es_with_oh(place, lang, raw_oh)
