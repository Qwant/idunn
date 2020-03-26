from idunn import settings
from .base import BaseBlock
from .opening_hour import OpeningHourBlock
from pydantic import constr
from typing import ClassVar, List, Optional


class Covid19Block(BaseBlock):
    BLOCK_TYPE: ClassVar = "covid19"
    STATUSES: ClassVar = ["open_as_usual", "open", "maybe_open", "closed", "unknown"]

    status: constr(regex="({})".format("|".join(STATUSES)))
    opening_hours: Optional[OpeningHourBlock]
    note: Optional[str]

    @classmethod
    def from_es(cls, es_poi, lang):
        if settings["BLOCK_COVID_ENABLED"] is not True:
            return None
        properties = es_poi.properties
        opening_hours = properties.get("opening_hours:covid19")
        status = "unknown"
        if opening_hours == "same":
            opening_hours = OpeningHourBlock.from_es(properties.get("opening_hours"), lang)
            status = "open_as_usual"
        elif opening_hours == "off":
            opening_hours = None
            status = "closed"
        elif opening_hours is not None:
            opening_hours = OpeningHourBlock.from_es(opening_hours, lang)
            if opening_hours is None:
                status = "unknown"
            elif opening_hours.status in ["open", "closed"]:
                if properties.get("opening_hours:covid19") == properties.get("opening_hours"):
                    status = "open_as_usual"
                else:
                    status = "open"
            else:
                status = "maybe_open"
        note = properties.get("note:covid19")

        return cls(status=status, note=note, opening_hours=opening_hours,)
