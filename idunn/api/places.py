import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import NotFound, BadRequest

from idunn.utils import prometheus
from idunn.utils.geom import get_geom, get_name
from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames

from idunn.api.pois import fetch_es_poi
from idunn.api.place import Place, LONG, SHORT, DEFAULT_VERBOSITY

from idunn.api.locations.poi import POI
from idunn.api.locations.admin import Admin
from idunn.api.locations.street import Street
from idunn.api.locations.address import Address

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

def fetch_es_place(id, es, indices, type) -> list:
    if type is None:
        index_name = "munin"
    elif type not in indices:
        raise BadRequest(
            status_code=400,
            detail={"message": f"Wrong type parameter: type={type}"}
        )
    else:
        index_name = indices.get(type)

    es_places = es.search(index=index_name,
        body={
            "filter": {
                "term": {"_id": id}
            }
        })

    es_place = es_places.get('hits', {}).get('hits', [])
    if len(es_place) == 0:
        raise NotFound(detail={'message': f"place {id} not found with type={type}"})

    return es_place

def get_place(id, es: Elasticsearch, indices: IndexNames, settings: Settings, lang=None, type=None, verbosity=DEFAULT_VERBOSITY) -> Place:
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

    return loader.load_place(es_place[0]['_source'], lang, settings, verbosity)
