from functools import lru_cache
from idunn import settings

if settings["MIMIR_ES_VERSION"] == "2":
    from elasticsearch import Elasticsearch, RequestsHttpConnection
elif settings["MIMIR_ES_VERSION"] == "7":
    from elasticsearch7 import Elasticsearch, RequestsHttpConnection
else:
    raise RuntimeError("Invalid MIMIR_ES_VERSION")


@lru_cache
def get_elasticsearch():
    kwargs = {}

    if settings["VERIFY_HTTPS"] is False:
        kwargs.update({"verify_certs": False, "connection_class": RequestsHttpConnection})

    return Elasticsearch(settings["MIMIR_ES"], **kwargs)
