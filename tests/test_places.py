import os
import json
import pytest
import urllib
from app import app
from apistar.test import TestClient

"""
    This module tests basic query against the endpoint '/places/'
"""

INDICES = {
    "admin": "munin_admin",
    "street": "munin_street",
    "addr": "munin_addr",
    "poi": "munin_poi"
}

def load_place(file_name, mimir_client, doc_type):
    """
    Load a json file in the elasticsearch and returns the corresponding Place id
    """

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
    load_place('admin_goujounac.json', mimir_client, 'admin')
    load_place('street_birnenweg.json', mimir_client, 'street')
    load_place('address_du_moulin.json', mimir_client, 'addr')
    load_place('orsay_museum.json', mimir_client, 'poi')

def test_basic_query_admin():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/admin:osm:relation:123057?lang=fr',
    )
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "admin:osm:relation:123057"
    assert resp["name"] == "Goujounac"
    assert resp["label"] == "Goujounac (46250), Lot, Occitanie, France"

def test_basic_query_street():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/35460343?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "35460343"
    assert resp["name"] == "9a Birnenweg"
    assert resp["label"] == "9a Birnenweg (Label)"

def test_basic_query_address():
    client = TestClient(app)
    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(
        url=f'http://localhost/v1/places/{id_moulin}?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "addr:5.108632;48.810273"
    assert resp["name"] == "4 Rue du Moulin"
    assert resp["label"] == "4 Rue du Moulin (Val-d'Ornain)"


def test_basic_query_poi():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/osm:way:63178753?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "osm:way:63178753"
    assert resp["name"] == "Musée d'Orsay"
    assert resp["local_name"] == "Musée d'Orsay"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["address"]["label"] == "62B Rue de Lille (Paris)"
    assert resp["blocks"][0]["type"] == "opening_hours"
    assert resp["blocks"][1]["type"] == "phone"
    assert resp["blocks"][0]["is_24_7"] == False

def test_type_query_admin():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/admin:osm:relation:123057?lang=fr&type=admin',
    )
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "admin:osm:relation:123057"
    assert resp["name"] == "Goujounac"
    assert resp["label"] == "Goujounac (46250), Lot, Occitanie, France"

def test_type_query_street():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/35460343?lang=fr&type=street',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "35460343"
    assert resp["name"] == "9a Birnenweg"
    assert resp["label"] == "9a Birnenweg (Label)"

def test_type_query_address():
    client = TestClient(app)
    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(
        url=f'http://localhost/v1/places/{id_moulin}?lang=fr&type=address',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "addr:5.108632;48.810273"
    assert resp["name"] == "4 Rue du Moulin"
    assert resp["label"] == "4 Rue du Moulin (Val-d'Ornain)"


def test_type_query_poi():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/osm:way:63178753?lang=fr&type=poi',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "osm:way:63178753"
    assert resp["name"] == "Musée d'Orsay"
    assert resp["local_name"] == "Musée d'Orsay"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["address"]["label"] == "62B Rue de Lille (Paris)"
    assert resp["blocks"][0]["type"] == "opening_hours"
    assert resp["blocks"][1]["type"] == "phone"
    assert resp["blocks"][0]["is_24_7"] == False

def test_type_unknown():
    client = TestClient(app)

    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(
        url=f'http://localhost/v1/places/{id_moulin}?lang=fr&type=globibulga',
    )
    assert response.status_code == 400
    assert response._content == b'{"message":"Wrong type parameter: type=globibulga"}'

def test_wrong_type():
    client = TestClient(app)

    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(
        url=f'http://localhost/v1/places/{id_moulin}?lang=fr&type=poi',
    )
    assert response.status_code == 404
    assert response._content == b'{"message":"place addr:5.108632;48.810273 not found with type=poi"}'
