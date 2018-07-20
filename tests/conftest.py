import pytest
from elasticsearch import Elasticsearch
from app import app
from idunn.utils.settings import SettingsComponent
from idunn.blocks.wikipedia import HTTPError40X


@pytest.fixture(scope='session')
def es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('elasticsearch')
    port = docker_services.wait_for_service("elasticsearch", 9200)

    url = f'http://{docker_services.docker_ip}:{port}'

    # we override the settings to set the ES_URL
    for c in app.injector.components:
        if isinstance(c, SettingsComponent):
            c._settings['ES_URL'] = url
    return url


@pytest.fixture(scope='session')
def es_client(es):
    return Elasticsearch([es])


@pytest.fixture(scope='session')
def wiki_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('wiki_es')
    port = docker_services.wait_for_service("wiki_es", 9200)

    url = f'http://{docker_services.docker_ip}:{port}'

    for c in app.injector.components:
        if isinstance(c, SettingsComponent):
            c._settings['WIKI_ES'] = url
            c._settings['ES_WIKI_LANG'] = 'fr'
    return url


@pytest.fixture(scope='session')
def wiki_es_client(wiki_es):
    return Elasticsearch([wiki_es])


@pytest.fixture(scope="session")
def init_indices(es_client, wiki_es_client):
    """
    Init the elastic index with the 'munin_poi_specific' index and alias it to 'munin_poi' as mimir does
    """
    index_name = 'munin_poi_specific'
    es_client.indices.create(index=index_name)
    es_client.indices.put_alias(name='munin_poi', index=index_name)

    index_name = 'wikidata_fr'
    wiki_es_client.indices.create(
        index=index_name,
        body={
            "mappings": {
                "wikipedia": {
                    "properties": {
                        "wikibase_item": {
                            "type": "string",
                            "analyzer": "keyword"
                        }
                    }
                }
            }
        }
    )
