import logging
from datetime import datetime
from typing import ClassVar, List
from enum import Enum
from pydantic import BaseModel, validator, ValidationError
from pytz import UTC
from requests import RequestException

from idunn import settings
from idunn.datasources.recycling import recycling_client
from .base import BaseBlock

logger = logging.getLogger(__name__)

MAX_DISTANCE_AROUND_POI = settings["RECYCLING_MAX_DISTANCE_AROUND_POI"]


def is_poi_in_finistere(poi):
    admins = poi.get_raw_admins()
    return any(
        any(c.get("name") == "ISO3166-2" and c.get("value") == "FR-29" for c in a.get("codes", []))
        for a in admins
    )


class ContainerType(str, Enum):
    recyclable = "recyclable"
    glass = "glass"
    unknown = "unknown"


class RecyclingContainer(BaseModel):
    updated_at: datetime
    filling_level: int
    type: ContainerType
    place_description: str

    @validator("type", pre=True)
    def container_type_fallback(cls, value):
        if value not in (t.value for t in ContainerType):
            return ContainerType.unknown
        return value

    @validator("updated_at")
    def validate_datetime(cls, dt):
        dt = dt.replace(microsecond=0)
        if dt.tzinfo is None:
            return UTC.localize(dt)
        return dt.astimezone(UTC)


class RecyclingBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "recycling"

    containers: List[RecyclingContainer]

    @classmethod
    def from_es(cls, place, lang):
        if not recycling_client.enabled:
            # Data source is not configured
            return None

        if place.PLACE_TYPE != "poi":
            return None

        if place.get_class_name() != "recycling":
            return None

        if not is_poi_in_finistere(place):
            return None

        try:
            containers = cls.fetch_containers(place)
        except (RequestException, ValidationError):
            logger.warning("Failed to fetch recycling containers data", exc_info=True)
            return None

        if not containers:
            return None
        return cls(containers=containers)

    @classmethod
    def fetch_containers(cls, place):
        coord = place.get_coord()
        if not coord:
            return []

        lat = coord.get("lat")
        lon = coord.get("lon")

        if lat is None or lon is None:
            return []

        hits = recycling_client.get_latest_measures(
            lat=lat, lon=lon, max_distance=MAX_DISTANCE_AROUND_POI
        )
        containers = []
        for h in hits:
            doc = h["_source"]

            if "percentage" not in doc:
                logger.warning(
                    "Recycling container data does not contain 'percentage' field",
                    extra={"doc": doc},
                )
                continue

            containers.append(
                RecyclingContainer(
                    type=doc.get("pav", {}).get("wasteType"),
                    updated_at=doc.get(settings.get("RECYCLING_DATA_TIMESTAMP_FIELD")),
                    filling_level=doc.get("percentage"),
                    place_description=doc.get("metadata", {}).get("entity"),
                )
            )
        return containers
