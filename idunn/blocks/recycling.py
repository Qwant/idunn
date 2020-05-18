from datetime import datetime, timedelta
from typing import ClassVar, List
from enum import Enum
import requests
from pydantic import BaseModel, validator
from pytz import UTC

from idunn import settings
from .base import BaseBlock


def is_poi_in_finistere(poi):
    admins = poi.get_raw_admins()
    return any(
        any(c.get("name") == "ISO3166-2" and c.get("value") == "FR-29" for c in a.get("codes", []))
        for a in admins
    )


class ContainerType(str, Enum):
    paper = "paper"
    glass = "glass"
    unknown = "unknown"


class RecyclingContainer(BaseModel):
    updated_at: datetime
    filling_level: int
    type: ContainerType

    @validator("updated_at")
    def validate_datetime(cls, dt):
        if dt.tzinfo is None:
            return UTC.localize(dt)
        return dt.as_timezone(UTC)


class RecyclingBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "recycling"

    containers: List[RecyclingContainer]

    @classmethod
    def from_es(cls, place, lang):
        if not settings.get("RECYCLING_SERVER_URL"):
            # Data source is not configured
            return None

        if place.PLACE_TYPE != "poi":
            return None

        if place.get_class_name() != "recycling":
            return None

        if not is_poi_in_finistere(place):
            return None

        # Fake data for testing purposes
        containers = [
            RecyclingContainer(type="glass", filling_level=30, updated_at="2020-05-16T17:38:12"),
            RecyclingContainer(
                type="paper",
                filling_level=60,
                updated_at=datetime.utcnow() - timedelta(days=1, minutes=10),
            ),
            RecyclingContainer(
                type="unknown",
                filling_level=90,
                updated_at=datetime.utcnow() - timedelta(seconds=20),
            ),
        ]

        return cls(containers=containers)

    @classmethod
    def fetch_container(cls, es_poi):
        """
        Unused at this point
        """
        if not es_poi.get_recycling() or settings.get("RECYCLING_SERVER_URL") is None:
            return None
        server_url = settings["RECYCLING_SERVER_URL"]
        if not server_url.endswith("/"):
            server_url += "/"
        try:
            args = {}
            if settings.get("KUZZLE_REQUEST_TIMEOUT") is not None:
                args["timeout"] = float(settings["KUZZLE_REQUEST_TIMEOUT"])
            res = requests.get(f"{server_url}{es_poi.get_id()}", **args)
            res = res.json()
            trash_volume = res.get("result", {}).get("_source", {}).get("volume")
            if trash_volume is None:
                return None
            trash_volume = float(trash_volume)
            trash_last_update = res.get("result", {}).get("_source", {}).get("hour")
        except Exception as e:
            # TODO: use logger
            print(f"failed to get information for trash {es_poi.get_id()}: {e}")
            return None
        return cls(volume=trash_volume, last_update=trash_last_update)
