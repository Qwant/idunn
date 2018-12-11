import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils import prometheus
from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import get_geom, get_name, fetch_es_place, LONG, SHORT, DEFAULT_VERBOSITY

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

def get_place(id, es: Elasticsearch, indices: IndexNames, settings: Settings, lang=None, type=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    """Main handler that returns the requested place"""
    if verbosity not in VERBOSITY_LEVELS:
        raise BadRequest(
            status_code=400,
            detail={"message": f"verbosity {verbosity} does not belong to the set of possible verbosity values={VERBOSITY_LEVELS}"}
        )

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    es_place = fetch_es_place(id, es, indices, type)

    places = {
        "admin": Admin,
        "street": Street,
        "addr": Address,
        "poi": POI,
    }

    loader = places.get(es_place[0].get('_type'))

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        logger.error("The place with the id {} has a wrong type: {}".format(id, es_place[0].get('_type')))
        return None

    place = PlaceData(es_place[0]['_source'])
    return loader.load_place(place, lang, settings, verbosity)
