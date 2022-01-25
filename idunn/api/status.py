import asyncio
import logging

import requests
from elasticsearch import ConnectionError

from idunn.datasources.pages_jaunes import pj_source
from idunn.datasources.wiki_es import WikiEs
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.places.exceptions import PlaceNotFound
from idunn.utils.es_wrapper import get_mimir_elasticsearch
from idunn import settings

ES_RUNNING_STATUS = ("green", "yellow")


class RequestsHTTPError:
    pass


def get_status():
    """Returns the status of the elastic cluster"""
    es_mimir_status = get_es_status(get_mimir_elasticsearch())

    info = WikiEs().get_info("Q7652", "fr")
    if info is not None:
        es_wiki_status = "up"
    else:
        es_wiki_status = "down"

    try:
        nlu_client.get_intentions(text="paris", lang="fr")
        nlp_status = "up"
    except NluClientException:
        nlp_status = "down"

    try:
        pj_source.get_place("pj:05360257")
        pj_status = "up"
    except PlaceNotFound:
        pj_status = "down"

    response = requests.get(settings["BRAGI_BASE_URL"] + "/status", verify=settings["VERIFY_HTTPS"])
    if "version" in response.json()["bragi"]:
        bragi_status = "up"
    else:
        bragi_status = "down"

    return {
        "info": {
            "es_mimir": es_mimir_status,
            "es_wiki": es_wiki_status,
            "bragi": bragi_status,
            "nlp": nlp_status,
            "pagesjaunes": pj_status,
        },
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
    return "down"
