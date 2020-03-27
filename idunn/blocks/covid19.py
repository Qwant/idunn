from idunn import settings
from idunn.utils.covid19_dataset import get_poi_covid_status
from .base import BaseBlock
from .opening_hour import OpeningHourBlock, parse_time_block
from pydantic import constr
from typing import ClassVar, Optional


class Covid19Block(BaseBlock):
    BLOCK_TYPE: ClassVar = "covid19"
    STATUSES: ClassVar = ["open_as_usual", "open", "maybe_open", "closed", "unknown"]

    status: constr(regex="({})".format("|".join(STATUSES)))
    opening_hours: Optional[OpeningHourBlock]
    note: Optional[str]

    @classmethod
    def from_es(cls, es_poi, lang):
        if es_poi.PLACE_TYPE != "poi":
            return None

        if settings["BLOCK_COVID_ENABLED"] is not True:
            return None

        properties = es_poi.properties
        found = False
        # Check if this is a french admin, otherwise we return nothing.
        for region in properties.get("administrative_regions", []):
            if region.get("zone_type") != "country":
                continue
            if "FR" in region.get("country_codes"):
                found = True
                break
        if not found:
            return None

        opening_hours = properties.get("opening_hours:covid19")
        note = es_poi.properties.get("note:covid19")
        status = "unknown"

        if opening_hours == "same":
            opening_hours = parse_time_block(OpeningHourBlock, es_poi, lang, properties.get("opening_hours"))
            status = "open_as_usual"
        elif opening_hours == "off":
            opening_hours = None
            status = "closed"
        elif opening_hours is not None:
            opening_hours = parse_time_block(OpeningHourBlock, es_poi, lang, opening_hours)
            if opening_hours is None:
                status = "unknown"
            elif opening_hours.status in ["open", "closed"]:
                if properties.get("opening_hours:covid19") == properties.get("opening_hours"):
                    status = "open_as_usual"
                else:
                    status = "open"
            else:
                status = "maybe_open"
        elif es_poi.get_meta().source == "osm" and settings["COVID19_USE_REDIS_DATASET"]:
            covid_status = get_poi_covid_status(es_poi.get_id())
            if covid_status is not None:
                if covid_status.opening_hours:
                    opening_hours = parse_time_block(OpeningHourBlock, es_poi, lang, covid_status.opening_hours)
                if covid_status.status in ("ouvert", "ouvert_adapté"):
                    status = "open"
                elif covid_status.status == "partial":
                    status = "maybe_open"
                elif covid_status.status == "fermé":
                    status = "closed"
                if not note:
                    note = covid_status.infos

        return cls(status=status, note=note, opening_hours=opening_hours,)
