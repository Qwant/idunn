import logging
from elasticsearch import ConnectionError  # pylint: disable=redefined-builtin

from idunn.utils.es_wrapper import get_elasticsearch

ES_RUNNING_STATUS = ("green", "yellow")


def get_status():
    """Returns the status of the elastic cluster
    """
    es = get_elasticsearch()
    try:
        cluster_health = es.cluster.health()
    except ConnectionError as err:
        logging.getLogger(__name__).error("Failed to connect to ES: %s", err)
        cluster_health = {}
        es_reachable = False
    else:
        es_reachable = True

    es_cluster_health = cluster_health.get("status") in ES_RUNNING_STATUS

    # the 'ready' is used as the readyness probe.
    # for the moment idunn is ready if ES is reachable
    ready = es_cluster_health
    return {"es": {"reachable": es_reachable, "running": es_cluster_health}, "ready": ready}
