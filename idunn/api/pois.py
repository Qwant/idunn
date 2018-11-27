from apistar.exceptions import NotFound
from elasticsearch import Elasticsearch

from idunn.api.poi import POI
from idunn.utils.settings import Settings


def fetch_es_poi(id, es) -> dict:
    es_pois = es.search(index='munin_poi',
                        body={
                            "filter": {
                                "term": {"_id": id}
                            }
                        })

    es_poi = es_pois.get('hits', {}).get('hits', [])
    if len(es_poi) == 0:
        raise NotFound(detail={'message': f"poi '{id}' not found"})
    result = es_poi[0]['_source']

    # Flatten properties into result
    properties = {p.get('key'): p.get('value') for p in result.get('properties')}
    result['properties'] = properties
    return result

def get_poi(id, es: Elasticsearch, settings: Settings, lang=None) -> POI:
    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    es_poi = fetch_es_poi(id, es)
    poi = POI.load_poi(es_poi, lang, "full")
    return poi
