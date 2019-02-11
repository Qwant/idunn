import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import get_geom, get_name, fetch_bbox_places, LONG, SHORT, DEFAULT_VERBOSITY_LIST, send_400

from apistar import http

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

def bbox_or_400(verbosity, bbox):
    if verbosity not in VERBOSITY_LEVELS:
        send_400(f"verbosity {verbosity} does not belong to the set of possible verbosity values={VERBOSITY_LEVELS}")
    if not bbox:
        send_400(f"the bounding box cannot be None")

    bbox = [float(c) for c in bbox.split(",")]
    left, bot, right, top = bbox[0], bbox[1], bbox[2], bbox[3]

    if not all(bbox):
        send_400(f"the bounding box is not complete")
    if left > right or bot > top:
        send_400(f"the bounding box is not valid")
    if left - right > 0.181:
        send_400(f"bounding box is too wide")
    if top - bot > 0.109:
        send_400(f"bounding box is too high")
    return bbox

def get_size(settings, size):
    max_size = settings['LIST_PLACES_MAX_SIZE']
    if size and int(size) < max_size:
        max_size = int(size)
    return max_size

def get_places_bbox(bbox, es: Elasticsearch, indices: IndexNames, settings: Settings, query_params: http.QueryParams, lang=None, verbosity=DEFAULT_VERBOSITY_LIST, size=None):
    """
        bbox = left,bottom,right,top
    """
    places_list = []
    params = dict(query_params)

    bbox = bbox_or_400(verbosity, params.get('bbox'))

    try:
        categories = params['categories']
    except KeyError:
        send_400(f"no category provided")

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    size = get_size(settings, size)

    bbox_places = fetch_bbox_places(bbox, es, indices, categories, size)

    for p in bbox_places:
        poi = POI.load_place(p['_source'], lang, settings, verbosity)
        places_list.append(poi)

    return {
        "places": places_list
    }
