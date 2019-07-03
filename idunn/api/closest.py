import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils import prometheus
from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import fetch_closest, DEFAULT_VERBOSITY, ALL_VERBOSITY_LEVELS
from idunn.api.pages_jaunes import pj_source

logger = logging.getLogger(__name__)


def closest_address(lat, lon, es: Elasticsearch, indices: IndexNames, settings: Settings, lang=None, verbosity=DEFAULT_VERBOSITY) -> Address:
    """Main handler that returns the requested place"""
    if verbosity not in ALL_VERBOSITY_LEVELS:
        raise BadRequest({
            "message": f"Unknown verbosity '{verbosity}'. Accepted values are {ALL_VERBOSITY_LEVELS}"
        })

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    es_addr = fetch_closest(lat, lon, 100, es)[0]

    places = {
        "addr": Address,
    }
    loader = places.get(es_addr.get('_type'))

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        raise Exception("Closest address to '{}:{}' has a wrong type: '{}'".format(lat, lon, es_addr.get('_type')))

    print('{} {}'.format(dir(es_addr), es_addr))
    return loader(es_addr['_source']).load_place(lang, verbosity)
