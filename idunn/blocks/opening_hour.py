import re
import logging
import datetime
from datetime import datetime
from pytz import country_timezones, timezone, UTC

from apistar import validators
from .base import BaseBlock

import humanized_opening_hours as hoh
from humanized_opening_hours.exceptions import ParseError, SpanOverMidnight
from tzwhere import tzwhere

"""
We load the tz structure once when Idunn starts since it's a time consuming step
"""
tz = tzwhere.tzwhere(forceTZ=True)

def get_tz(es_poi):
    """
    Returns the timezone corresponding to the coordinates of the POI.

    >>> get_tz({}) is None
    True

    >>> get_tz({'coord':{"lon": None, "lat": 48.858260156496016}}) is None
    True

    >>> get_tz({'coord':{"lon": 2.2944990157640612, "lat": None}}) is None
    True

    >>> get_tz({'coord':{"lon": 2.2944990157640612, "lat": 48.858260156496016}})
    <DstTzInfo 'Europe/Paris' LMT+0:09:00 STD>
    """
    if 'coord' in es_poi:
        coord = es_poi.get('coord')
        lon = coord.get('lon')
        lat = coord.get('lat')
        if lon is not None and lat is not None:
            return timezone(tz.tzNameAt(lat, lon))
    return None

class OpeningHourBlock(BaseBlock):
    BLOCK_TYPE = 'opening_hours'

    status = validators.String()
    next_transition_datetime = validators.String()
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

        try:
            clean_oh = hoh.OHParser.sanitize(raw)
            oh = hoh.OHParser(clean_oh)
        except ParseError:
            logging.info("Failed to parse OSM opening_hour field", exc_info=True)
            return None
        except SpanOverMidnight: # In the current hoh version (branch 'new-parsing' of the repo) opening hours are not allowed to span over midnight
                                 # However in the coming version this feature will be supported
                                 # TODO: remove this catch when this will be released
            logging.info("OSM opening_hour field cannot span over midnight", exc_info=True)
            return None

        status = 'close'
        next_transition_datetime = ''
        time_before_next = 0
        poi_tz = get_tz(es_poi)
        if poi_tz is not None:
            poi_dt = UTC.localize(datetime.utcnow()).astimezone(poi_tz)
            # The current version of the hoh lib doesn't allow to use the next_change() function
            # with an offset aware datetime.
            # This is why we replace the timezone info until this problem is fixed in the library.
            nt = oh.next_change(allow_recursion=False, moment=poi_dt.replace(tzinfo=None))
            # Then we localize the next_change transition datetime in the local POI timezone.
            next_transition = poi_tz.localize(nt.replace(tzinfo=None))

            next_transition_datetime = next_transition.isoformat()
            delta = next_transition - poi_dt
            time_before_next = int(delta.total_seconds())
            if oh.is_open(poi_dt):
                status = 'open'

        return cls(
            status=status,
            next_transition_datetime=next_transition_datetime,
            seconds_before_next_transition=time_before_next,
            is_24_7=is247,
            raw=raw,
            days=[] # TODO: format to be defined
        )
