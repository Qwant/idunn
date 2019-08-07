import logging
import requests

from apistar import validators
from .base import BaseBlock
from idunn.api.kuzzle import kuzzle_client
from apistar.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AirQuality(BaseBlock):
    BLOCK_TYPE = "Environment"

    air_quality = validators.Object(allow_null=True)

    @classmethod
    def from_es(cls, es_poi, lang):
        print(es_poi.PLACE_TYPE)
        if es_poi.PLACE_TYPE != 'admin':
            return None
        if 'city' in es_poi.get('zone_type') or es_poi.get('zone_type') == 'suburb':
            air_quality = get_air_quality(es_poi.get('bbox'))
        else:
            return None

        if not air_quality:
            return None

        return cls(
            air_quality=air_quality
        )


def get_air_quality(geobbox):
    if not kuzzle_client.enabled:
        raise HTTPException("Kuzzle client is not available", status_code=501)

    air_quality_res = kuzzle_client.fetch_air_quality(geobbox)

    return air_quality_res

