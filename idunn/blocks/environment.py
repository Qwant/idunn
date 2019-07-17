import logging
import requests

from apistar import validators
from .base import BaseBlock
from idunn import settings

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
    kuzzle_address = settings.get('KUZZLE_CLUSTER_ADDRESS')
    kuzzle_port = settings.get('KUZZLE_CLUSTER_PORT')
    print(geobbox)
    if not kuzzle_address or not kuzzle_port:
        logger.warning(f"Missing kuzzle address or port")
        return None

    if not geobbox:
        logger.warning(f"Missing geobox")
        return None

    top = geobbox[3]
    left = geobbox[0]
    bottom = geobbox[1]
    right = geobbox[2]

    url_kuzzle = kuzzle_address + ':' + kuzzle_port+'/eea/air_pollution/_search'
    print(url_kuzzle)
    query = {
        "query": {
            "bool": {
                "must": [{
                    "term": {
                        "date": "now-6h/h"
                    }
                }],
                "filter": [{
                    "geo_bounding_box": {
                        "geo_loc": {
                            "top": top,
                            "left": left,
                            "bottom": bottom,
                            "right": right

                        }
                    }
                }]
            }
        },
        "aggregations": {
            "PM10": {
                "avg": {"field": "PM10"}
            },
            "O3": {
                "avg": {"field": "O3"}
            },
            "NO2": {
                "avg": {"field": "NO2"}
            },
            "SO2": {
                "avg": {"field": "SO2"}
            },
            "PM2.5": {
                "avg": {"field": "PM25"}
            }
        }
    }

    res = requests.post(url_kuzzle, json=query)
    res = res.json()
    res = res.get('result', {}).get('aggregations', {})

    return res

