from apistar.exceptions import NotFound
from elasticsearch import Elasticsearch

from idunn.api.poi import POI
from idunn.api.pois import fetch_es_poi
from idunn.api.place import Place, Admin, Street, Address
from idunn.utils.settings import Settings

def get_index(type, settings):
    return {
        "admin": settings['PLACE_ADMIN_INDEX'],
        "street": settings['PLACE_STREET_INDEX'],
        "address": settings['PLACE_ADDRESS_INDEX'],
        "poi": settings['PLACE_POI_INDEX'],
    }.get(type, "_all")


def fetch_es_place(id, es, settings, index_name) -> dict:
    es_places = es.search(index=index_name,
        body={
            "filter": {
                "term": {"_id": id}
            }
        })

    es_place = es_places.get('hits', {}).get('hits', [])
    if len(es_place) == 0:
        raise NotFound(detail={'message': f"place '{id}' not found"})

    return es_place

def load_admin(es_place, lang, settings):
    return Admin.load_place(es_place, lang, settings)

def load_street(es_place, lang, settings):
    return Street.load_place(es_place, lang, settings)

def load_address(es_place, lang, settings):
    return Address.load_place(es_place, lang, settings)

def load_poi(es_place, lang, settings):
    properties = {p.get('key'): p.get('value') for p in es_place.get('properties')}
    es_place['properties'] = properties
    return POI.load_place(es_place, lang, settings)

def get_place(id, es: Elasticsearch, settings: Settings, lang=None, type=None) -> Place:
    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    index_name = get_index(type, settings)
    es_place = fetch_es_place(id, es, settings, index_name)

    loader = {
        "munin_adm": load_admin,
        "munin_str": load_street,
        "munin_add": load_address,
        "munin_poi": load_poi,
    }

    place = loader.get(es_place[0].get('_index')[:9])

    if place is None:
        return None

    return place(es_place[0]['_source'], lang, settings)
