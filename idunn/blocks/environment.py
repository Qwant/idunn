import logging
import requests
from apistar.exceptions import HTTPException

from apistar import validators
from .base import BaseBlock
from idunn import settings

logger = logging.getLogger(__name__)



class Environment(BaseBlock):
    BLOCK_TYPE = "Environment"

    air_quality = validators.Object(allow_null=True)

    @classmethod
    def get_air_quality(cls, geobbox):
        kuzzle_address = settings.get('KUZZLE_CLUSTER_ADDRESS')
        kuzzle_port = settings.get('KUZZLE_CLUSTER_PORT')

        if not kuzzle_address or not kuzzle_port:
            raise HTTPException(f"Missing kuzzle address or port", status_code=501)

        # geo = requests.get('https://www.qwant.com/maps/geocoder/autocomplete?q='+cityName)
        # geobbox = geo.get('features')[0].get('properties').get('geocoding').get('bbox')
        print(geobbox)
        top = geobbox[3]
        left = geobbox[0]
        bottom = geobbox[1]
        right = geobbox[2]

        print(top)
        print(left)
        print(bottom)
        print(right)
        url_kuzzle = 'http://'+kuzzle_address+':'+kuzzle_port+'/eea/air_pollution/_search'
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
        print(res)
        air_quality = res.get('result', {}).get('aggregations', {})
        print(air_quality)
        return cls(
            air_quality=air_quality,
        )
