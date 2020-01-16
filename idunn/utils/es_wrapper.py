from elasticsearch import Elasticsearch, RequestsHttpConnection
from idunn import settings

ES_CONNECTION = None

def get_elasticsearch():
    global ES_CONNECTION
    debug_params = {}

    if ES_CONNECTION is None:
        if settings["DEBUG"]:
            debug_params["verify_certs"] = False
            debug_params["connection_class"] = RequestsHttpConnection
        ES_CONNECTION = Elasticsearch(settings["MIMIR_ES"], **debug_params)
    return ES_CONNECTION
