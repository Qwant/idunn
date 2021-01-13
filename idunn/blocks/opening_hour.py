import logging
from datetime import datetime, timedelta, date
from pytz import timezone, utc
from tzwhere import tzwhere
from pydantic import BaseModel, Schema, conint, constr
from typing import ClassVar, List, Literal, Optional

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


def get_coord(es_poi):
    """
    Returns the coordinates from the POI json
    """
    coord = es_poi.get_coord()
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
        days.append(
            {
                "dayofweek": day.isoweekday(),
                "local_date": day.isoformat(),
                "status": OPEN if oh.is_open_at_date(day) else CLOSED,
                "opening_hours": [
                    {"beginning": start.strftime("%H:%M"), "end": end.strftime("%H:%M")}
                    for start, end, _unknown, _comment in oh.get_open_intervals_at_date(
                        day, overlap_next_day=True
                    )
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
        is_24_7 = oh.is_24_7(curr_dt)
        return cls(
            status=status,
            next_transition_datetime=next_transition_datetime if not is_24_7 else None,
            seconds_before_next_transition=time_before_next if not is_24_7 else None,
            is_24_7=is_24_7,
            raw=raw,
            days=get_days(oh, curr_dt),
        )

    @staticmethod
    def get_raw_oh(es_poi):
        return es_poi.get_raw_opening_hours()

    @classmethod
    def from_es(cls, es_poi, lang, raw_oh=None):
        if not raw_oh:
            raw_oh = cls.get_raw_oh(es_poi)

        if not raw_oh:
            return None

        # Fallback to London coordinates if POI coordinates are not known.
        poi_lat, poi_lon = get_coord(es_poi) or (51.5, 0)
        poi_country_code = es_poi.get_country_code()

        poi_tzname = tz.tzNameAt(poi_lat, poi_lon, forceTZ=True)
        poi_tz = get_tz(poi_tzname, poi_lat, poi_lon)

        if poi_tz is None:
            logger.info("No timezone found for poi %s", es_poi.get("id"))
            return None

        oh = OpeningHours(raw_oh, poi_tz, poi_country_code)
        curr_dt = utc.localize(datetime.utcnow())

        if not oh.validate():
            logger.info(
                "Failed to validate opening_hours field, id:'%s' raw:'%s'",
                es_poi.get_id(),
                raw_oh,
                exc_info=True,
            )
            return None

        if oh.is_open(curr_dt):
            status = OPEN
        else:
            status = CLOSED

        if cls == OpeningHourBlock and oh.is_24_7(curr_dt):
            return cls.init_class(status, None, None, oh, curr_dt, raw_oh)

        next_transition = oh.next_change(curr_dt)

        if next_transition is None:
            return None

        # Then we localize the next_change transition datetime in the local POI timezone.
        next_transition = round_dt_to_minute(next_transition)
        delta = next_transition - curr_dt
        time_before_next = int(delta.total_seconds())

        return cls.init_class(
            status, next_transition.isoformat(), time_before_next, oh, curr_dt, raw_oh
        )


class HappyHourBlock(OpeningHourBlock):
    type: Literal["happy_hours"] = "happy_hours"

    @staticmethod
    def get_raw_oh(es_poi):
        return es_poi.get_raw_happy_hours()
