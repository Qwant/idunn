import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils import prometheus
from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import fetch_es_place, DEFAULT_VERBOSITY, ALL_VERBOSITY_LEVELS
from idunn.api.pages_jaunes import pj_source

logger = logging.getLogger(__name__)


def get_place(id, es: Elasticsearch, indices: IndexNames, settings: Settings, lang=None, type=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    """Main handler that returns the requested place"""
    if verbosity not in ALL_VERBOSITY_LEVELS:
        raise BadRequest({
            "message": f"Unknown verbosity '{verbosity}'. Accepted values are {ALL_VERBOSITY_LEVELS}"
        })

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

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
