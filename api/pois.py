import os

from apistar.exceptions import NotFound
from elasticsearch import Elasticsearch
from apistar_settings import Settings


def fetch_es_poi(id, es_url) -> dict:
    es = Elasticsearch([es_url])
    es_pois = es.search(index='munin_poi',
                        body={
                            "filter": {
                                "term": {"_id": id}
                            }
                        })

    es_poi = es_pois.get('hits', {}).get('hits', [])
    if len(es_poi) == 0:
        raise NotFound(detail={'message': f"poi '{id}' not found"})
    return es_poi[0]['_source']


def make_response(es_poi, lang) -> dict:
    poi = {
        'name': es_poi['name'],
        'id': es_poi['id'],
        'label': es_poi['label'],
    }
    # TODO!
    return poi


def get_poi(id, settings: Settings, lang=None):
    es_poi = fetch_es_poi(id, settings['ES_URL'])

    return make_response(es_poi, lang)
