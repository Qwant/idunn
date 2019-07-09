import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn import settings
from idunn.utils import prometheus
from idunn.places import Street, Address
from idunn.api.utils import fetch_closest, DEFAULT_VERBOSITY, ALL_VERBOSITY_LEVELS

logger = logging.getLogger(__name__)


MAX_DISTANCE_IN_METERS = 500

def get_closest_place(lat: float, lon: float, es: Elasticsearch):
    es_addr = fetch_closest(lat, lon, es=es, max_distance=MAX_DISTANCE_IN_METERS)

    places = {
        "addr": Address,
        "street": Street,
    }
    loader = places.get(es_addr.get('_type'))

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        raise Exception("Closest address to '{}:{}' has a wrong type: '{}'".format(lat, lon, es_addr.get('_type')))

    return loader(es_addr['_source'])


def closest_address(lat: float, lon: float, es: Elasticsearch, lang=None, verbosity=DEFAULT_VERBOSITY) -> Address:
    """Main handler that returns the requested place"""
    if verbosity not in ALL_VERBOSITY_LEVELS:
        raise BadRequest({
            "message": f"Unknown verbosity '{verbosity}'. Accepted values are {ALL_VERBOSITY_LEVELS}"
        })

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    place = get_closest_place(lat, lon, es)
    return place.load_place(lang, verbosity)
