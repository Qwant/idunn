import pytest
import responses
import re
from elasticsearch import Elasticsearch
from app import app, settings
from idunn.utils.settings import SettingsComponent
from idunn.blocks.wikipedia import HTTPError40X
from idunn.blocks.wikipedia import WikipediaLimiter
import time
from .utils import override_settings


@pytest.fixture(scope='session')
def mimir_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('mimir_es')
    port = docker_services.wait_for_service("mimir_es", 9200)
    url = f'http://{docker_services.docker_ip}:{port}'

    # we override the settings to set the MIMIR_ES
    with override_settings({'MIMIR_ES': url}):
        yield url

@pytest.fixture(scope='session')
def mimir_client(mimir_es):
    return Elasticsearch([mimir_es])


@pytest.fixture(scope='session')
def wiki_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start('wiki_es')
    port = docker_services.wait_for_service("wiki_es", 9200)
    url = f'http://{docker_services.docker_ip}:{port}'

    with override_settings({'WIKI_ES': url, 'ES_WIKI_LANG': 'fr'}):
        yield url

@pytest.fixture(scope='session')
def wiki_client(wiki_es):
    return Elasticsearch([wiki_es])


@pytest.fixture(scope='function')
def wiki_es_ko(docker_services):
    port = docker_services.wait_for_service("wiki_es", 9200)
    url = "something.invalid:1234"

    with override_settings({'WIKI_ES': url, 'ES_WIKI_LANG': 'fr'}):
        yield url

@pytest.fixture(scope='function')
def wiki_client_ko(wiki_es_ko):
    return Elasticsearch([wiki_es_ko])


@pytest.fixture(scope="session")
def init_indices(mimir_client, wiki_client):
    """
    Init the elastic index with the 'munin_poi_specific' index and alias it to 'munin_poi' as mimir does
    """
    mimir_client.indices.create(index='munin_poi')
    mimir_client.indices.put_alias(name='munin', index='munin_poi')

    mimir_client.indices.create(index='munin_addr')
    mimir_client.indices.put_alias(name='munin', index='munin_addr')

    mimir_client.indices.create(index='munin_street')
    mimir_client.indices.put_alias(name='munin', index='munin_street')

    mimir_client.indices.create(index='munin_admin')
    mimir_client.indices.put_alias(name='munin', index='munin_admin')

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

@pytest.fixture(scope="module", autouse=True)
def mock_external_requests():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
                 re.compile(r'^https://.*\.wikipedia.org/'),
                 status=404)
        yield

@pytest.fixture(scope='session')
def redis(docker_services):
    """Ensure that Redis is up and responsive."""
    docker_services.start('wiki_redis')
    port = docker_services.port_for("wiki_redis", 6379)

    url = f'{docker_services.docker_ip}:{port}'

    return url
