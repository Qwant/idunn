import pytest
import os
from elasticsearch import Elasticsearch


@pytest.fixture(scope='session')
def es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('elasticsearch')
    port = docker_services.wait_for_service("elasticsearch", 9200)

    url = f'http://{docker_services.docker_ip}:{port}'

    os.environ['ES_URL'] = url

    return url


@pytest.fixture(scope='session')
def es_client(es):
    return Elasticsearch([es])
