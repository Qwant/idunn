import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest, NotFound

from idunn import settings
from idunn.utils import prometheus
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI, Latlon
from idunn.api.utils import fetch_es_place, DEFAULT_VERBOSITY, ALL_VERBOSITY_LEVELS
from idunn.api.pages_jaunes import pj_source
from .closest import get_closest_place

logger = logging.getLogger(__name__)


def validate_verbosity(verbosity):
    if verbosity not in ALL_VERBOSITY_LEVELS:
        raise BadRequest({
            "message": f"Unknown verbosity '{verbosity}'. Accepted values are {ALL_VERBOSITY_LEVELS}"
        })
    return verbosity

def validate_lang(lang):
    if not lang:
        return settings['DEFAULT_LANGUAGE']
    return lang.lower()

def get_place(id, es: Elasticsearch, indices: IndexNames, lang=None, type=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    """Main handler that returns the requested place"""
    verbosity = validate_verbosity(verbosity)
    lang = validate_lang(lang)

    if id.startswith(pj_source.PLACE_ID_PREFIX):
        pj_place = pj_source.get_place(id)
        return pj_place.load_place(lang, verbosity)

    es_place = fetch_es_place(id, es, indices, type)

    places = {
        "admin": Admin,
        "street": Street,
        "addr": Address,
        "poi": POI,
    }
    loader = places.get(es_place.get('_type'))

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        raise Exception("Place with id '{}' has a wrong type: '{}'".format(id, es_place[0].get('_type')))

    return loader(es_place['_source']).load_place(lang, verbosity)


def get_place_latlon(lat: float, lon: float, es: Elasticsearch, lang=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    verbosity = validate_verbosity(verbosity)
    lang = validate_lang(lang)
    try:
        closest_place = get_closest_place(lat, lon, es)
    except NotFound:
        closest_place = None
    place = Latlon(lat, lon, closest_address=closest_place)
    return place.load_place(lang, verbosity)
