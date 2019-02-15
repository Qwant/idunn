import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import get_geom, get_name, fetch_bbox_places, LONG, SHORT, DEFAULT_VERBOSITY_LIST, InvalidBbox, NoFilter, BadVerbosity

from apistar import http

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

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

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    if verbosity not in VERBOSITY_LEVELS:
        raise BadVerbosity

    try:
        categories = params['raw_filter[]']
    except KeyError:
        raise NoFilter

    try:
        bbox = params['bbox']
    except KeyError:
        raise InvalidBbox

    size = get_size(settings, size)

    bbox_places = fetch_bbox_places(bbox, es, indices, categories, size)

    for p in bbox_places:
        poi = POI.load_place(p['_source'], lang, settings, verbosity)
        places_list.append(poi)

    return {
        "places": places_list
    }
