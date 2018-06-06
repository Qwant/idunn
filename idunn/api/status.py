import logging
from elasticsearch import Elasticsearch, ConnectionError


ES_RUNNING_STATUS = ('green', 'yellow')

def get_status(es: Elasticsearch):
    try:
        cluster_health = es.cluster.health()
    except ConnectionError as err:
        logging.error('Failed to connect to ES: %s', err)
        cluster_health = {}

    return {
        'es': {
            'running': cluster_health.get('status') in ES_RUNNING_STATUS
        }
    }
