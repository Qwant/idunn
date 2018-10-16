from apistar.test import TestClient
from app import app
import pytest
import json
import os

"""
    This module tests basic query against the endpoint '/places/'
"""

def load_place(file_name, mimir_client, index_name, _doc_type):
    """
    Load a json file in the elasticsearch and returns the corresponding Place id
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', file_name)
    with open(filepath, "r") as f:
        place = json.load(f)
        place_id = place['id']
        mimir_client.index(index=index_name,
                        body=place,
                        doc_type=_doc_type, # 'admin', 'street', 'addr' or 'poi'
                        id=place_id,
                        refresh=True)
        return place_id

@pytest.fixture(scope="session")
def admin_goujounac(mimir_client, init_indices):
    """
    fill elasticsearch with an admin
    """
    return load_place('admin_goujounac.json', mimir_client, 'munin_admin_test', 'admin')

@pytest.fixture(scope="session")
def street_birnenweg(mimir_client, init_indices):
    """
    fill elasticsearch with a street
    """
    return load_place('street_birnenweg.json', mimir_client, 'munin_street_test', 'street')

@pytest.fixture(scope="session")
def address_du_moulin(mimir_client, init_indices):
    """
    fill elasticsearch with an address
    """
    return load_place('address_du_moulin.json', mimir_client, 'munin_addr_test', 'addr')

@pytest.fixture(scope="session")
def orsay_museum(mimir_client, init_indices):
    """
    fill elasticsearch with the orsay museum
    """
    return load_place('orsay_museum.json', mimir_client, 'munin_poi', 'poi')


def test_basic_query_admin(admin_goujounac):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/{admin_goujounac}?lang=fr',
    )
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "admin:osm:relation:123057"
    assert resp["name"] == "Goujounac"
    assert resp["label"] == "Goujounac (46250), Lot, Occitanie, France"

def test_basic_query_street(street_birnenweg):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/{street_birnenweg}?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "35460343"
    assert resp["name"] == "9a Birnenweg"
    assert resp["label"] == "9a Birnenweg"

def ko_test_basic_query_address(address_du_moulin):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/"{address_du_moulin}"?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp["id"] == "addr:5.108632;48.810273"
    assert resp["name"] == "4 Rue du Moulin"
    assert resp["label"] == "4 Rue du Moulin (Val-d'Ornain)"


def test_basic_query_poi(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places/{orsay_museum}?lang=fr',
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


