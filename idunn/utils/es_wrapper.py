from functools import lru_cache
from idunn import settings

from elasticsearch import Elasticsearch, RequestsHttpConnection


@lru_cache
def get_elasticsearch():
    kwargs = {}

    if settings["VERIFY_HTTPS"] is False:
        kwargs.update({"verify_certs": False, "connection_class": RequestsHttpConnection})

    return Elasticsearch(settings["MIMIR_ES"], **kwargs)
