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
    BLOCK_TYPE: ClassVar = 'air_quality'

    CO: Optional[ParticleType]
    PM10: Optional[ParticleType]
    O3: Optional[ParticleType]
    NO2: Optional[ParticleType]
    SO2: Optional[ParticleType]
    PM2_5: Optional[ParticleType]
    quality_index: conint(ge=1, le=5)
    date: datetime
    source: str
    source_url: str
    measurements_unit: Optional[str] = None


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
        for x in ['CO', 'PM10', 'O3', 'NO2', 'SO2', 'PM2_5']:
            if x not in air_quality:
                continue
            entry = air_quality.get(x)
            print(entry)
            if entry == {} or (entry['value'] is None and entry['quality_index'] is None):
                air_quality[x] = None

        return cls(**air_quality)


def get_air_quality(geobbox):
    if not kuzzle_client.enabled:
        return None
    return kuzzle_client.fetch_air_quality(geobbox)
