from elasticsearch import Elasticsearch
from idunn import settings

ES_CONNECTION = None


def get_elasticsearch():
    global ES_CONNECTION

    if ES_CONNECTION is None:
        ES_CONNECTION = Elasticsearch(settings['MIMIR_ES'])
    return ES_CONNECTION
