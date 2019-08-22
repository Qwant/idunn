import requests
import logging
from apistar.exceptions import HTTPException

from idunn import settings
logger = logging.getLogger(__name__)

scale = {
    'CO': [5, 10, 25, 50],
    'PM2_5': [10, 20, 25, 50],
    'PM10': [20, 35, 50, 100],
    'NO2': [40, 100, 200, 400],
    'O3': [80, 120, 180, 240],
    'SO2': [100, 200, 350, 500]
}

def enrichRes(res):
    """
    Return pollutantes value with pollution indice and global air_quality indice
    """
    enrichData = {}
    globalQuality = 0
    for particles, value in res.items():
        valueNumber = value.get("value")
        if valueNumber is None:
            enrichData[particles] = {}
            continue
        scaleP = scale[particles]
        scaleIndiceLength = len(scaleP) - 1
        while scaleIndiceLength >= 0:
            if (valueNumber > scaleP[scaleIndiceLength]):
                break
            scaleIndiceLength -= 1

        enrichData[particles] = {"value": valueNumber, "quality_index": scaleIndiceLength + 2}
        globalQuality = max(globalQuality, scaleIndiceLength + 2)
    enrichData['quality_index'] = globalQuality

    return enrichData

def moreInfo(info):
    """
    get more info about air quality
    :param data received from kuzzle:
    :return: object last update, source name, measurements_unit
    """

    source = info[0].get('_source').get('source', '')
    source_url = "http://airindex.eea.europa.eu/" if source.startswith("EEA") else ''

    return {
        "date": info[0].get('_source').get('update_at'),
        "source": source,
        "source_url": source_url,
        "measurements_unit": info[0].get('_source').get('measurements_unit')
    }



class KuzzleClient:
    def __init__(self):
        self.session = requests.Session()
        self.request_timeout = float(settings['KUZZLE_REQUEST_TIMEOUT'])

    @property
    def kuzzle_url(self):
        return settings.get('KUZZLE_CLUSTER_URL')

    @property
    def enabled(self):
        return bool(self.kuzzle_url)

    def fetch_event_places(self, bbox, size) -> list:
        if not self.enabled:
            raise Exception('Kuzzle is not enabled')

        left, bot, right, top = bbox[0], bbox[1], bbox[2], bbox[3]

        url_kuzzle = f'{self.kuzzle_url}/opendatasoft/events/_search'
        query = {
            'query': {
                'bool': {
                    'filter': {
                        'geo_bounding_box': {
                            'geo_loc': {
                                'top_left': {
                                    'lat':  top,
                                    'lon':  left
                                },
                                'bottom_right': {
                                    'lat': bot,
                                    'lon': right
                                }
                            }
                        }
                    },
                    'must': {
                        'range': {
                            'date_end': {
                                'gte': 'now/d',
                                'lte': 'now+31d/d'
                            }
                        }
                    }
                }
            },
            'size': size
        }
        bbox_places = self.session.post(url_kuzzle, json=query, timeout=self.request_timeout)
        bbox_places.raise_for_status()
        try:
            bbox_places = bbox_places.json()
        except Exception:
            logger.error(f'Error with kuzzle JSON with request to {url_kuzzle} '
                         f'Got {bbox_places.content}', exc_info=True)
            raise HTTPException(detail='kuzzle error', status_code=503)

        bbox_places = bbox_places.get('result', {}).get('hits', [])
        return bbox_places


    def fetch_air_quality(self, geobbox) -> dict:
        """
        fetch air_quality inside polygon
        :param geobbox: coordinate of the admin
        :return:
        """
        if not self.enabled:
            raise Exception('Kuzzle is not enabled')

        top = geobbox[3]
        left = geobbox[0]
        bottom = geobbox[1]
        right = geobbox[2]

        url_kuzzle = f'{self.kuzzle_url}/opendatasoft/air_quality/_search'
        query = {
            "query": {
                "bool": {
                    "filter": [{
                        "geo_bounding_box": {
                            "geo_loc": {
                                "top": top,
                                "left": left,
                                "bottom": bottom,
                                "right": right
                            }
                        }
                    }, {
                        "range": {
                            "update_at": {
                                "gte": "now-5h/h"
                            }
                        }}]
                }
            },
            "aggregations": {
                "CO": {
                    "avg": {"field": "CO"}
                },
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
                "PM2_5": {
                    "avg": {"field": "PM2_5"}
                }
            },
            "sort": [{
                "update_at": "desc"
            }]
        }

        res = self.session.post(url_kuzzle, json=query, timeout=self.request_timeout)
        res.raise_for_status()
        res = res.json()
        globalInfo = res.get('result', {}).get('hits', [])
        res = res.get('result', {}).get('aggregations', {})
        if all(v is None for v in res.values()):
            return {}

        res = enrichRes(res)
        res.update(moreInfo(globalInfo))
        return res

kuzzle_client = KuzzleClient()
