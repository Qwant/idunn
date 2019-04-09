import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import NotFound

from idunn import settings
from idunn.places import PjPOI
from idunn.utils.geometry import bbox_inside_polygon, france_polygon

logger = logging.getLogger(__name__)


class PjSource:
    PLACE_ID_PREFIX = 'pj:'

    es_index = settings.get('PJ_ES_INDEX')
    es_query_template = settings.get('PJ_ES_QUERY_TEMPLATE')

    def __init__(self):
        pj_es_url = settings.get('PJ_ES')

        if pj_es_url:
            self.es = Elasticsearch(pj_es_url, timeout=3.)
            self.enabled = True
        else:
            self.enabled = False

    def bbox_is_covered(self, bbox):
        if not self.enabled:
            return False
        return bbox_inside_polygon(*bbox, poly=france_polygon)

    def get_places_bbox(self, raw_categories, bbox, size=10):
        left, bot, right, top = bbox

        result = self.es.search_template(
            index=self.es_index,
            body={
                'id': self.es_query_template,
                'params': {
                    'query': '',
                    'top_left_lat':  top,
                    'top_left_lon': left,
                    'bottom_right_lat': bot,
                    'bottom_right_lon': right,
                    'filter_category': True,
                    'category': raw_categories,
                },
            },
            params={
                'size': size
            }
        )
        raw_places = result.get('hits', {}).get('hits', [])
        return [PjPOI(p['_source']) for p in raw_places]

    def get_place(self, id):
        internal_id = id.replace(self.PLACE_ID_PREFIX, '', 1)

        es_places = self.es.search(
            index=self.es_index,
            body={
                "filter": {
                    "term": {"_id": internal_id}
                }
            }
        )

        es_place = es_places.get('hits', {}).get('hits', [])
        if len(es_place) == 0:
            raise NotFound(detail={'message': f"place {id} not found"})
        if len(es_place) > 1:
            logger.warning("Got multiple places with id %s", id)
        return PjPOI(es_place[0]['_source'])


pj_source = PjSource()
