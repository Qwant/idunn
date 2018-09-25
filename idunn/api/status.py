import logging
from elasticsearch import Elasticsearch, ConnectionError


ES_RUNNING_STATUS = ('green', 'yellow')

def get_status(es: Elasticsearch):
    try:
        cluster_health = es.cluster.health()
    except ConnectionError as err:
        logging.getLogger(__name__).error('Failed to connect to ES: %s', err)
        cluster_health = {}
        es_reachable = False
    else:
        es_reachable = True

    return {
        'es': {
            'reachable': es_reachable,
            'running': cluster_health.get('status') in ES_RUNNING_STATUS
        }
    }
