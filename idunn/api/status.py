from elasticsearch import Elasticsearch


ES_RUNNING_STATUS = ('green', 'yellow')

def get_status(es: Elasticsearch):
    cluster_health = es.cluster.health()
    return {
        'es': {
            'running': cluster_health.get('status') in ES_RUNNING_STATUS
        }
    }
