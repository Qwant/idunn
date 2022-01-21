import logging
from elasticsearch import ConnectionError

from idunn.datasources import wiki_es
from idunn.datasources.pages_jaunes import pj_source
from idunn.geocoder.nlu_client import nlu_client
from idunn.utils.es_wrapper import get_mimir_elasticsearch, get_wiki_elasticsearch

ES_RUNNING_STATUS = ("green", "yellow")


class RequestsHTTPError:
    pass


def get_status():
    """Returns the status of the elastic cluster"""
    es_mimir_status = get_es_status(get_mimir_elasticsearch())
    try:
        wiki_es.WikiEs.get_info("Q7652")
        es_wiki_status = "up"
    except:
        es_wiki_status = "down"

    try:
        nlu_client.get_intentions(text="paris", lang="fr")
        nlp_status = "up"
    except:
        nlp_status = "down"

    try:
        pj_source.get_place("pj:05360257")
        pj_status = "up"
    except:
        pj_status = "down"

    return {
        "info": [
            {"es_mimir": es_mimir_status},
            {"es_wiki": es_wiki_status},
            {"nlp": nlp_status},
            {"pagesjaunes": pj_status},
        ]
    }


def get_es_status(es):
    try:
        cluster_health = es.cluster.health()
    except ConnectionError as err:
        logging.getLogger(__name__).error("Failed to connect to ES: %s", err)
        return "down"
    else:
        es_reachable = True
    es_cluster_health = cluster_health.get("status") in ES_RUNNING_STATUS
    if es_reachable and es_cluster_health:
        return "up"
    else:
        return "down"
