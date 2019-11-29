import logging
from pydantic import BaseModel, conint
from datetime import datetime
from typing import ClassVar, Optional
from redis import Redis, RedisError

from idunn import settings
from idunn.api.kuzzle import kuzzle_client
from .base import BaseBlock

from idunn.utils.redis import get_redis_pool


logger = logging.getLogger(__name__)

DISABLED_STATE = object() # Used to flag cache as disabled by settings


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


def get_air_quality(geobbox):
    if not kuzzle_client.enabled:
        return None
    return kuzzle_client.fetch_air_quality(geobbox)


class Weather(BaseBlock):
    BLOCK_TYPE = 'weather'

    temperature = validators.Number(allow_null=True)
    icon = validators.String(
        allow_null=True,
        enum=['11d', '09d', '10d', '13d', '50d', '01d', '01n', '02d', '03d', '04d', '02n', '03n', '04n']
    )
    _connection = None

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

    @classmethod
    def set_value(cls, key, json_result):
        try:
            cls._connection.set(key, json_result, ex=cls._expire)
        except RedisError:
            prometheus.exception("RedisError")
            logging.exception("Got a RedisError")

    @classmethod
    def get_value(cls, key):
        try:
            value_stored = cls._connection.get(key)
            return value_stored
        except RedisError as exc:
            prometheus.exception("RedisError")
            logging.exception("Got a RedisError")
            raise CacheNotAvailable from exc

    @classmethod
    def init_cache(cls):
        cls._expire = int(settings['WIKI_CACHE_TIMEOUT'])  # seconds
        redis_db = settings['WIKI_CACHE_REDIS_DB']
        try:
            redis_pool = get_redis_pool(db=redis_db)
        except RedisNotConfigured:
            logger.warning("No Redis URL has been set for caching", exc_info=True)
            cls._connection = DISABLED_STATE
        else:
            cls._connection = Redis(connection_pool=redis_pool)

    @classmethod
    def cache_it(cls, key, f):
        """
        Takes function f and put its result in a redis cache.
        It requires a prefix string to identify the name
        of the function cached.
        """
        if cls._connection is None:
            cls.init_cache()

        def with_cache(*args, **kwargs):
            """
            If the redis is up we use the cache,
            otherwise we bypass it
            """
            if cls._connection is not DISABLED_STATE:
                try:
                    value_stored = cls.get_value(key)
                except CacheNotAvailable:
                    # Cache is not reachable: we don't want to execute 'f'
                    # (and fetch wikipedia content, possibly very often)
                    return None
                if value_stored is not None:
                    return json.loads(value_stored.decode('utf-8'))
                result = f(*args, **kwargs)
                json_result = json.dumps(result)
                cls.set_value(key, json_result)
                return result
            return f(*args, **kwargs)
        return with_cache


def get_local_weather(coord):
    def inner(coord):
        return weather_client.fetch_weather_places(coord)

    if not weather_client.enabled:
        return None
    wiki_poi_info = Weather.cache_it(coord, inner)(coord)
