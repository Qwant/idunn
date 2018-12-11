import os
import json
import pytest
from app import app
from apistar.test import TestClient

INDICES = {
    "admin": "munin_admin",
    "street": "munin_street",
    "addr": "munin_addr",
    "poi": "munin_poi"
}

def load_place(file_name, mimir_client, doc_type):
    index_name = INDICES.get(doc_type)

    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', file_name)
    with open(filepath, "r") as f:
        place = json.load(f)
        place_id = place['id']
        mimir_client.index(index=index_name,
                        body=place,
                        doc_type=doc_type, # 'admin', 'street', 'addr' or 'poi'
                        id=place_id,
                        refresh=True)

@pytest.fixture(autouse=True)
def load_all(mimir_client, init_indices):
    load_place('orsay_museum.json', mimir_client, 'poi')

@pytest.fixture(scope="session", autouse=True)
def orsay_wiki_es(wiki_client, init_indices):
    """
    We load the wiki_es fixture for the orsay museum
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'orsay_wiki_es.json')
    with open(filepath, "r") as f:
        poi = json.load(f)
        poi_id = poi['id']
        wiki_client.index(index='wikidata_fr',
                        body=poi,
                        doc_type='wikipedia',
                        id=poi_id,
                        refresh=True)
        return poi_id

def test_orsay_images():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/osm:way:63178753?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["blocks"][4]["type"] == "images"

    assert resp["blocks"][4]["images"] == [
        {
          "url": "https://qwant.com/thumbr/900/f/c/09ccd097b398526403a1bda0016d2e1385f0f9d7d2b069ee4b4221c9c5e3ed/1024px-Logo_musée_d'Orsay.png?u=https%253A%252F%252Fupload.wikimedia.org%252Fwikipedia%252Ffr%252Fthumb%252F7%252F73%252FLogo_mus%2525C3%2525A9e_d%252527Orsay.png%252F1024px-Logo_mus%2525C3%2525A9e_d%252527Orsay.png&q=0&b=1&p=0&a=0",
          "alt": "Musée d'Orsay",
          "credits": "wikimedia"
        },
        {
          "url": "https://qwant.com/thumbr/225/9/6/a33bf3566fe4bb2189c652aba5da1d3cac58b91eaa0ad0007acee4a33653bb/1024px-Logo_musée_d'Orsay.png?u=https%253A%252F%252Fupload.wikimedia.org%252Fwikipedia%252Ffr%252Fthumb%252F7%252F73%252FLogo_mus%2525C3%2525A9e_d%252527Orsay.png%252F1024px-Logo_mus%2525C3%2525A9e_d%252527Orsay.png&q=0&b=1&p=0&a=0",
          "alt": "Musée d'Orsay",
          "credits": "wikimedia"
        }
    ]
