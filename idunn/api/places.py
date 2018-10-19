import logging
from apistar.exceptions import NotFound, BadRequest
from elasticsearch import Elasticsearch

from idunn.api.poi import POI
from idunn.api.pois import fetch_es_poi
from idunn.api.place import Place, Admin, Street, Address
from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames

logger = logging.getLogger(__name__)

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
        raise NotFound(detail={'message': f"place '{id}' not found with type='{type}'"})

    return es_place

def get_place(id, es: Elasticsearch, indices: IndexNames, settings: Settings, lang=None, type=None) -> Place:
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
        return None

    return loader.load_place(es_place[0]['_source'], lang, settings)
