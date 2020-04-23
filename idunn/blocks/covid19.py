import logging
from enum import Enum
from typing import ClassVar, Optional

from idunn import settings
from idunn.utils.covid19_dataset import get_poi_covid_status
from .base import BaseBlock
from .opening_hour import OpeningHourBlock, parse_time_block


logger = logging.getLogger(__name__)
COVID19_BLOCK_COUNTRIES = settings["COVID19_BLOCK_COUNTRIES"].split(",")


class CovidOpeningStatus(str, Enum):
    open_as_usual = "open_as_usual"
    open = "open"
    maybe_open = "maybe_open"
    closed = "closed"
    unknown = "unknown"


class Covid19Block(BaseBlock):
    BLOCK_TYPE: ClassVar = "covid19"

    status: CovidOpeningStatus
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
        if es_poi.get_country_code() not in COVID19_BLOCK_COUNTRIES:
            return None

        opening_hours = None
        note = es_poi.properties.get("description:covid19")
        status = CovidOpeningStatus.unknown
        contribute_url = None

        raw_opening_hours = properties.get("opening_hours:covid19")
        covid_status_from_redis = None

        if es_poi.get_meta().source == "osm" and settings["COVID19_USE_REDIS_DATASET"]:
            covid_status_from_redis = get_poi_covid_status(es_poi.get_id())

        if covid_status_from_redis is not None:
            contribute_url = cls.get_ca_reste_ouvert_url(es_poi)
            note = covid_status_from_redis.infos or None

            if covid_status_from_redis.opening_hours:
                opening_hours = parse_time_block(
                    OpeningHourBlock, es_poi, lang, covid_status_from_redis.opening_hours
                )

            if covid_status_from_redis.status == "ouvert":
                status = CovidOpeningStatus.open_as_usual
            elif covid_status_from_redis.status == "ouvert_adapté":
                status = CovidOpeningStatus.open
            elif covid_status_from_redis.status == "partiel":
                status = CovidOpeningStatus.maybe_open
            elif covid_status_from_redis.status == "fermé":
                status = CovidOpeningStatus.closed

        elif raw_opening_hours == "same":
            opening_hours = parse_time_block(
                OpeningHourBlock, es_poi, lang, properties.get("opening_hours")
            )
            status = CovidOpeningStatus.open_as_usual
        elif raw_opening_hours == "open":
            status = CovidOpeningStatus.open
        elif raw_opening_hours == "restricted":
            status = CovidOpeningStatus.maybe_open
        elif raw_opening_hours == "off":
            status = CovidOpeningStatus.closed
        elif raw_opening_hours is not None:
            opening_hours = parse_time_block(OpeningHourBlock, es_poi, lang, opening_hours)
            if opening_hours is None:
                status = "unknown"
            elif opening_hours.status in ["open", "closed"]:
                if raw_opening_hours == properties.get("opening_hours"):
                    status = CovidOpeningStatus.open_as_usual
                else:
                    status = CovidOpeningStatus.open
            else:
                status = CovidOpeningStatus.maybe_open

        return cls(
            status=status, note=note, opening_hours=opening_hours, contribute_url=contribute_url
        )
