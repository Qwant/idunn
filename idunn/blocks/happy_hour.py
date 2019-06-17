import logging
from datetime import datetime, timedelta, date
from pytz import timezone, UTC
from apistar import validators, types
from tzwhere import tzwhere
import humanized_opening_hours as hoh
from humanized_opening_hours.exceptions import HOHError

from .base import BaseBlock
from .opening_hour import get_tz, get_coord, tz


logger = logging.getLogger(__name__)


class HappyHoursType(types.Type):
    beginning = validators.String()
    end = validators.String()


class DaysType(types.Type):
    dayofweek = validators.Integer(minimum=1, maximum=7)
    local_date = validators.Date()
    status = validators.String(enum=['yes', 'no'])
    happy_hours = validators.Array(items=HappyHoursType)


class HappyHourBlock(BaseBlock):
    BLOCK_TYPE = 'happy_hours'

    status = validators.String(enum=['yes', 'no'])
    next_transition_datetime = validators.String(allow_null=True)
    seconds_before_next_transition = validators.Integer(allow_null=True)
    raw = validators.String()
    days = validators.Array(items=DaysType)

    @classmethod
    def from_es(cls, es_poi, lang):
        raw = es_poi.get_raw_happy_hours()
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
        except HOHError:
            logger.info(
                "Failed to parse happy_hours field, id:'%s' raw:'%s'",
                es_poi.get_id(), raw, exc_info=True
            )
            return None

        poi_dt = UTC.localize(datetime.utcnow()).astimezone(poi_tz)

        if oh.is_open(poi_dt.replace(tzinfo=None)):
            status = 'yes'
        else:
            status = 'no'

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
        next_transition = cls.round_dt_to_minute(next_transition)

        next_transition_datetime = next_transition.isoformat()
        delta = next_transition - poi_dt
        time_before_next = int(delta.total_seconds())

        return cls(
            status=status,
            next_transition_datetime=next_transition_datetime,
            seconds_before_next_transition=time_before_next,
            raw=oh.field,
            days=cls.get_days(oh, dt=poi_dt)
        )

    @staticmethod
    def round_dt_to_minute(dt):
        dt += timedelta(seconds=30)
        return dt.replace(second=0, microsecond=0)

    @staticmethod
    def round_time_to_minute(t):
        dt = datetime.combine(date(2000,1,1), t)
        rounded = HappyHourBlock.round_dt_to_minute(dt)
        return rounded.time()

    @classmethod
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
                'status': 'yes' if len(periods) > 0 else 'no',
                'happy_hours': []
            }
            for beginning_dt, end_dt in periods:
                if beginning_dt.date() < day:
                    continue
                beginning = cls.round_time_to_minute(beginning_dt.time())
                end = cls.round_time_to_minute(end_dt.time())
                day_value['happy_hours'].append(
                    {
                        'beginning': beginning.strftime('%H:%M'),
                        'end': end.strftime('%H:%M')
                    }
                )
            days.append(day_value)
        return days
