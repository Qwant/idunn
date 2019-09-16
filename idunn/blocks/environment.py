import logging
from pydantic import BaseModel, conint
from datetime import datetime
from typing import ClassVar, Optional

from idunn import settings
from idunn.api.kuzzle import kuzzle_client
from .base import BaseBlock


logger = logging.getLogger(__name__)


class ParticleType(BaseModel):
    value: float
    quality_index: Optional[conint(ge=1, le=5)]


class AirQuality(BaseBlock):
    BLOCK_TYPE: ClassVar = "air_quality"

    CO: Optional[ParticleType] = None
    PM10: Optional[ParticleType] = None
    O3: Optional[ParticleType] = None
    NO2: Optional[ParticleType] = None
    SO2: Optional[ParticleType] = None
    PM2_5: Optional[ParticleType] = None
    quality_index: conint(ge=1, le=5)
    date: datetime
    source: str
    source_url: str
    measurements_unit: Optional[str] = None

    @classmethod
    def from_es(cls, place, lang):
        if not settings["BLOCK_AIR_QUALITY_ENABLED"]:
            return None
        if place.PLACE_TYPE != "admin":
            return None
        if place.get("zone_type") not in ("city", "city_district", "suburb"):
            return None

        bbox = place.get_bbox()
        if not bbox:
            return None

        try:
            air_quality = get_air_quality(bbox)
        except Exception:
            logger.warning("Failed to fetch air quality for %s", place.get_id(), exc_info=True)
            return None

        if not air_quality:
            return None
        for x in ["CO", "PM10", "O3", "NO2", "SO2", "PM2_5"]:
            if x not in air_quality:
                continue
            entry = air_quality.get(x)
            if entry == {} or entry.get("value") is None:
                air_quality[x] = None

        return cls(**air_quality)


class Weather(BaseBlock):
    BLOCK_TYPE = 'weather'

    temperature = validators.Number(allow_null=True)
    icon = validators.String(
        allow_null=True,
        enum=['11d', '09d', '10d', '13d', '50d', '01d', '01n', '02d', '03d', '04d', '02n', '03n', '04n']
    )

    @classmethod
    def from_es(cls, place, lang):
        if place.PLACE_TYPE != 'admin':
            return None
        if place.get('zone_type') not in ('city', 'city_district', 'suburd'):
            return None

        coord = place.get_coord()
        if not coord:
            return None

        try:
            weather = get_local_weather(coord)
        except Exception:
            logger.warning('Failed to fetch weather for %s', place.get_id(), exc_info=True)
            return None

        if not weather:
            return None

        return cls(**weather)


def get_air_quality(geobbox):
    if not kuzzle_client.enabled:
        return None
    return kuzzle_client.fetch_air_quality(geobbox)


def get_local_weather(coord):
    if not weather_client.enabled:
        return None
    return weather_client.fetch_weather_places(coord)
