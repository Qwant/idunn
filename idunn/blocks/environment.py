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

    CO: ParticleType
    PM10: ParticleType
    O3: ParticleType
    NO2: ParticleType
    SO2: ParticleType
    PM2_5: ParticleType
    quality_index: conint(ge=1, le=5)
    date: datetime
    source: str
    source_url: str
    measurements_unit: Optional[str]


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


def get_air_quality(geobbox):
    if not kuzzle_client.enabled:
        return None
    return kuzzle_client.fetch_air_quality(geobbox)
