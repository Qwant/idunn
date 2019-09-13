import logging
from apistar.types import Type
from apistar import validators

from idunn import settings
from idunn.api.kuzzle import kuzzle_client
from idunn.api.weather import weather_client
from apistar.types import Type
from .base import BaseBlock


logger = logging.getLogger(__name__)


class ParticleType(Type):
    value = validators.Number(allow_null=True)
    quality_index = validators.Integer(minimum=1, maximum=5, allow_null=True)


class AirQuality(BaseBlock):
    BLOCK_TYPE = 'air_quality'

    CO = ParticleType
    PM10 = ParticleType
    O3 = ParticleType
    NO2 = ParticleType
    SO2 = ParticleType
    PM2_5 = ParticleType
    quality_index = validators.Integer(minimum=1, maximum=5)
    date = validators.DateTime()
    source = validators.String()
    source_url = validators.String()
    measurements_unit = validators.String(allow_null=True)


    @classmethod
    def from_es(cls, place, lang):
        if not settings['BLOCK_AIR_QUALITY_ENABLED']:
            return None
        if place.PLACE_TYPE != 'admin':
            return None
        if place.get('zone_type') not in ('city', 'city_district', 'suburb'):
            return None

        bbox = place.get_bbox()
        if not bbox:
            return None

        try:
            air_quality = get_air_quality(bbox)
        except Exception:
            logger.warning('Failed to fetch air quality for %s', place.get_id(), exc_info=True)
            return None

        if not air_quality:
            return None

        return cls(**air_quality)


class Weather(BaseBlock):
    BLOCK_TYPE = 'weather'

    temperature = validators.Number(allow_null=True)
    weatherPic = validators.String(allow_null=True)

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
