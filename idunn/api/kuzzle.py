import requests
import logging
from apistar.exceptions import HTTPException

from idunn import settings
logger = logging.getLogger(__name__)

class KuzzleClient:
    def __init__(self):
        self.session = requests.Session()

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
        bbox_places = self.session.post(url_kuzzle, json=query)
        bbox_places.raise_for_status()
        try:
            bbox_places = bbox_places.json()
        except Exception:
            logger.error(f'Error with kuzzle JSON with request to {url_kuzzle} '
                         f'Got {bbox_places.content}', exc_info=True)
            raise HTTPException(status_code=503)

        bbox_places = bbox_places.get('result', {}).get('hits', [])
        return bbox_places

kuzzle_client = KuzzleClient()
