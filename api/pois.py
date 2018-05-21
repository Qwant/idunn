from elasticsearch import Elasticsearch
import os


def fetch_es_poi(id) -> dict:
    es_url = os.environ['ES_URL']  # TODO better configure this
    es = Elasticsearch([es_url])
    es_poi = es.get(id=id, index='munin_poi')

    return es_poi['_source']


def make_response(es_poi, lang) -> dict:
    poi = {
        'name': es_poi['name'],
        'id': es_poi['id'],
        'label': es_poi['label'],
    }
    # TODO!
    return poi


def get_poi(id, lang):
    es_poi = fetch_es_poi(id)

    return make_response(es_poi, lang)
