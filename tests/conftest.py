import pytest
from elasticsearch import Elasticsearch
from app import app, settings
from idunn.utils.settings import SettingsComponent
from idunn.blocks.wikipedia import HTTPError40X


@pytest.fixture(scope='session')
def mimir_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('mimir_es')
    port = docker_services.wait_for_service("mimir_es", 9200)

    url = f'http://{docker_services.docker_ip}:{port}'

    # we override the settings to set the MIMIR_ES
    settings._settings['MIMIR_ES'] = url
    return url

@pytest.fixture(scope='session')
def mimir_client(mimir_es):
    return Elasticsearch([mimir_es])

@pytest.fixture(scope='session')
def wiki_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('wiki_es')
    port = docker_services.wait_for_service("wiki_es", 9200)

    url = f'http://{docker_services.docker_ip}:{port}'

    settings._settings['WIKI_ES'] = url
    settings._settings['ES_WIKI_LANG'] = 'fr'
    return url


@pytest.fixture(scope='session')
def wiki_client(wiki_es):
    return Elasticsearch([wiki_es])

@pytest.fixture(scope="session")
def init_indices(mimir_client, wiki_client):
    """
    Init the elastic index with the 'munin_poi_specific' index and alias it to 'munin_poi' as mimir does
    """
    index_name = 'munin_poi_specific'
    mimir_client.indices.create(index=index_name)
    mimir_client.indices.put_alias(name='munin_poi', index=index_name)

    index_name = 'wikidata_fr'
    wiki_client.indices.create(
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
