import logging
from typing import ClassVar, Optional, Literal

from pydantic import BaseModel, conint, constr

from idunn.datasources.weather import weather_client
from idunn.utils.redis import RedisWrapperWeather
from .base import BaseBlock

logger = logging.getLogger(__name__)

DISABLED_STATE = object()  # Used to flag cache as disabled by settings


class ParticleType(BaseModel):
    value: float
    quality_index: Optional[conint(ge=1, le=5)]


class Weather(BaseBlock):
    type: Literal["weather"] = "weather"
    temperature: Optional[float] = None
    icon: Optional[constr(regex="11d|09d|10d|13d|50d|01d|01n|02d|03d|04d|02n|03n|04n")]
    _connection: ClassVar = None

    @classmethod
    def from_es(cls, place, lang):
        if place.PLACE_TYPE != "admin":
            return None
        if place.get("zone_type") not in ("city", "city_district", "suburd"):
            return None

        coord = place.get_coord()
        if not coord:
            return None

        try:
            weather = get_local_weather(coord)
        except Exception:
            logger.warning("Failed to fetch weather for %s", place.get_id(), exc_info=True)
            return None

        if not weather:
            return None

        return cls(**weather)


def get_local_weather(coord):
    def inner(coord):
        return weather_client.fetch_weather_places(coord)

    if not weather_client.enabled:
        return None
    key = f"weather_{coord['lat']}_{coord['lon']}"
    return RedisWrapperWeather.cache_it(key, inner)(coord)
