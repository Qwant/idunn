import pytest
import os
from elasticsearch import Elasticsearch
from app import app
from utils.settings import SettingsComponent


@pytest.fixture(scope='session')
def es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('elasticsearch')
    port = docker_services.wait_for_service("elasticsearch", 9200)

    url = f'http://{docker_services.docker_ip}:{port}'

    # we override the settings to set the ES_URL
    for c in app.injector.components:
        if isinstance(c, SettingsComponent):
            c['ES_URL'] = url
    return url


@pytest.fixture(scope='session')
def es_client(es):
    return Elasticsearch([es])
