import os
import json
import pytest
import respx
from elasticsearch import Elasticsearch

from .utils import init_wikidata_es, override_settings


@pytest.fixture(scope="session")
def mimir_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start("mimir_es")
    port = docker_services.wait_for_service("mimir_es", 9200)
    url = f"http://{docker_services.docker_ip}:{port}"

    # we override the settings to set the MIMIR_ES
    with override_settings({"MIMIR_ES": url}):
        yield url


@pytest.fixture(scope="session")
def mimir_client(mimir_es):
    return Elasticsearch([mimir_es])


@pytest.fixture(scope="session")
def wiki_es(docker_services):
    """Ensure that ES is up and responsive."""
    docker_services.start("wiki_es")
    port = docker_services.wait_for_service("wiki_es", 9200)
    url = f"http://{docker_services.docker_ip}:{port}"

    with override_settings({"WIKI_ES": url, "ES_WIKI_LANG": "fr"}), init_wikidata_es():
        yield url


@pytest.fixture(scope="session")
def wiki_client(wiki_es):
    return Elasticsearch([wiki_es])


@pytest.fixture(scope="function")
def wiki_es_ko(docker_services):
    docker_services.wait_for_service("wiki_es", 9200)
    url = "something.invalid:1234"

    with override_settings({"WIKI_ES": url, "ES_WIKI_LANG": "fr"}), init_wikidata_es():
        yield url


@pytest.fixture(scope="function")
def wiki_es_undefined():
    with override_settings({"WIKI_ES": None}), init_wikidata_es():
        yield


@pytest.fixture(scope="function")
def wiki_client_ko(wiki_es_ko):
    return Elasticsearch([wiki_es_ko])


@pytest.fixture(scope="session")
def init_indices(mimir_client, wiki_client):
    """
    Init the elastic index with the 'munin_poi_specific' index and alias it to 'munin_poi' as mimir
    does.
    """
    mimir_client.indices.create(
        index="munin_poi",
        body={
            "mappings": {
                "poi": {
                    "properties": {
                        "coord": {
                            "type": "geo_point",
                            "lat_lon": True,
                            "geohash": True,
                            "geohash_prefix": True,
                            "geohash_precision": 11,
                        },
                        "weight": {"type": "double"},
                    }
                },
                "poi_type": {
                    "properties": {
                        "name": {"type": "string", "index_options": "docs", "analyzer": "word"}
                    }
                },
            },
            "settings": {
                "index": {
                    "analysis": {
                        "analyzer": {
                            "word": {
                                "filter": ["lowercase", "asciifolding"],
                                "type": "custom",
                                "tokenizer": "standard",
                            }
                        }
                    }
                }
            },
        },
    )
    mimir_client.indices.put_alias(name="munin", index="munin_poi")

    mimir_client.indices.create(
        index="munin_addr",
        body={
            "mappings": {
                "addr": {
                    "properties": {
                        "coord": {
                            "type": "geo_point",
                            "lat_lon": True,
                            "geohash": True,
                            "geohash_prefix": True,
                            "geohash_precision": 11,
                        },
                    }
                }
            }
        },
    )
    mimir_client.indices.put_alias(name="munin", index="munin_addr")

    mimir_client.indices.create(
        index="munin_street",
        body={
            "mappings": {
                "street": {
                    "properties": {
                        "coord": {
                            "type": "geo_point",
                            "lat_lon": True,
                            "geohash": True,
                            "geohash_prefix": True,
                            "geohash_precision": 11,
                        },
                    }
                }
            }
        },
    )
    mimir_client.indices.put_alias(name="munin", index="munin_street")

    mimir_client.indices.create(index="munin_admin")
    mimir_client.indices.put_alias(name="munin", index="munin_admin")

    index_name = "wikidata_fr"
    wiki_client.indices.create(
        index=index_name,
        body={
            "mappings": {
                "wikipedia": {
                    "properties": {"wikibase_item": {"type": "string", "analyzer": "keyword"}}
                }
            }
        },
    )


@pytest.fixture(scope="session")
def redis(docker_services):
    """Ensure that Redis is up and responsive."""
    docker_services.start("wiki_redis")
    port = docker_services.port_for("wiki_redis", 6379)

    url = f"{docker_services.docker_ip}:{port}"

    return url


INDICES = {
    "admin": "munin_admin",
    "street": "munin_street",
    "addr": "munin_addr",
    "poi": "munin_poi",
}


def load_place(file_name, mimir_client, doc_type="poi"):
    """
    Load a json file in the elasticsearch
    """
    index_name = INDICES.get(doc_type)

    filepath = os.path.join(os.path.dirname(__file__), "fixtures", file_name)
    with open(filepath, "r") as f:
        place = json.load(f)
        place_id = place["id"]
        mimir_client.index(
            index=index_name,
            body=place,
            doc_type=doc_type,  # 'admin', 'street', 'addr' or 'poi'
            id=place_id,
            refresh=True,
        )


@pytest.fixture(autouse=True, scope="session")
def load_all(mimir_client, init_indices):
    load_place("patisserie_peron.json", mimir_client)
    load_place("orsay_museum.json", mimir_client)
    load_place("blancs_manteaux.json", mimir_client)
    load_place("louvre_museum.json", mimir_client)
    load_place("cinema_multiplexe.json", mimir_client)
    load_place("fake_all_blocks.json", mimir_client)
    load_place("basket_ball.json", mimir_client)
    load_place("recycling.json", mimir_client)
    load_place("recycling_not_in_bretagne.json", mimir_client)
    load_place("creperie.json", mimir_client)
    load_place("admin_goujounac.json", mimir_client, doc_type="admin")
    load_place("street_birnenweg.json", mimir_client, doc_type="street")
    load_place("address_du_moulin.json", mimir_client, doc_type="addr")
    load_place("address_43_rue_de_paris.json", mimir_client, doc_type="addr")
    load_place("admin_dunkerque.json", mimir_client, doc_type="admin")
    load_place("admin_paris.json", mimir_client, doc_type="admin")


@pytest.fixture
def httpx_mock():
    with respx.mock(assert_all_called=False) as rsps:
        yield rsps
