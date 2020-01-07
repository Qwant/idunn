from elasticsearch import Elasticsearch, RequestsHttpConnection
from idunn import settings

ES_CONNECTION = None


def get_elasticsearch():
    global ES_CONNECTION

    if ES_CONNECTION is None:
        if settings["MIMIR_ES_VERIFY_HTTPS"] is False:
            ES_CONNECTION = Elasticsearch(settings["MIMIR_ES"],
                                          verify_certs=False,
                                          connection_class=RequestsHttpConnection)
        else:
            ES_CONNECTION = Elasticsearch(settings["MIMIR_ES"])
    return ES_CONNECTION
