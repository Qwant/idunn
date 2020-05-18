from datetime import datetime, timezone
from pydantic.json import ENCODERS_BY_TYPE
import pytz


def override_datetime_encoder():
    default_datetime_formatter = ENCODERS_BY_TYPE[datetime]

    def custom_dt_formatter(dt):
        if dt.tzinfo in (timezone.utc, pytz.UTC):
            return default_datetime_formatter(dt).replace("+00:00", "Z")
        return default_datetime_formatter(dt)

    ENCODERS_BY_TYPE[datetime] = custom_dt_formatter
