import logging
from idunn import settings
from idunn.utils.covid19_dataset import get_poi_covid_status
from .base import BaseBlock
from .opening_hour import OpeningHourBlock, parse_time_block
from pydantic import constr
from typing import ClassVar, Optional

logger = logging.getLogger(__name__)


class Covid19Block(BaseBlock):
    BLOCK_TYPE: ClassVar = "covid19"
    STATUSES: ClassVar = ["open_as_usual", "open", "maybe_open", "closed", "unknown"]

    status: constr(regex="^({})$".format("|".join(STATUSES)))
    opening_hours: Optional[OpeningHourBlock]
    note: Optional[str]
    contribute_url: Optional[str]

    @classmethod
    def get_ca_reste_ouvert_url(cls, place):
        try:
            _, osm_type, osm_id = place.get_id().split(":")
            cro_id = f"{osm_type[0]}{osm_id}"
        except Exception:
            logger.warning("Failed to build caresteouvert id for %s", place.get_id())
            return None
        lat = place.get_coord()["lat"]
        lon = place.get_coord()["lon"]
        return f"https://www.caresteouvert.fr/@{lat:.6f},{lon:.6f},17/place/{cro_id}"

    @classmethod
    def from_es(cls, es_poi, lang):
        if es_poi.PLACE_TYPE != "poi":
            return None

        if settings["BLOCK_COVID_ENABLED"] is not True:
            return None

        properties = es_poi.properties
        # Check if this is a french admin, otherwise we return nothing.
        if "FR" not in es_poi.get_country_codes():
            return None

        opening_hours = properties.get("opening_hours:covid19")
        note = es_poi.properties.get("description:covid19")
        status = "unknown"

        contribute_url = None
        covid_status = None
        if es_poi.get_meta().source == "osm" and settings["COVID19_USE_REDIS_DATASET"]:
            covid_status = get_poi_covid_status(es_poi.get_id())
            if covid_status is not None:
                contribute_url = cls.get_ca_reste_ouvert_url(es_poi)

        if opening_hours == "same":
            opening_hours = parse_time_block(
                OpeningHourBlock, es_poi, lang, properties.get("opening_hours")
            )
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
        elif covid_status is not None:
            if covid_status.opening_hours:
                opening_hours = parse_time_block(
                    OpeningHourBlock, es_poi, lang, covid_status.opening_hours
                )
            if covid_status.status == "ouvert":
                status = "open_as_usual"
            elif covid_status.status == "ouvert_adapté":
                status = "open"
            elif covid_status.status == "partiel":
                status = "maybe_open"
            elif covid_status.status == "fermé":
                status = "closed"
            if not note:
                note = covid_status.infos or None

        return cls(
            status=status, note=note, opening_hours=opening_hours, contribute_url=contribute_url
        )
