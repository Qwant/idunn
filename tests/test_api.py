from apistar.test import TestClient
from app import app
import pytest
import json
import os

@pytest.fixture(scope="module")
def init_indices(es_client):
    index_name = 'munin_poi_specific'
    es_client.indices.create(index=index_name)
    es_client.indices.put_alias(name='munin_poi', index=index_name)

def load_poi(file_name, es_client):
    """
    Load a json file in the elasticsearch and returns the corresponding POI id
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', file_name)
    with open(filepath, "r") as f:
        poi = json.load(f)
        poi_id = poi['id']
        es_client.index(index='munin_poi',
                        body=poi,
                        doc_type='poi',
                        id=poi_id,
                        refresh=True)
        return poi_id

@pytest.fixture(scope="module")
def orsay_museum(es_client):
    """
    fill elasticsearch with one poi, the orsay museum
    """
    # we load the poi in 'munin_poi_specific' index and alias it to 'munin_poi' to have a architecture like mimir
    return load_poi('orsay_museum.json', es_client)

@pytest.fixture(scope="module")
def blancs_manteaux(es_client):
    """
    fill elasticsearch with one poi, the church des blancs manteaux
    """
    return load_poi('blancs_manteaux.json', es_client)

def test_basic_query(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{orsay_museum}',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:way:63178753'
    assert resp['name'] == "Musée d'Orsay"
    assert resp['local_name'] == "Musée d'Orsay"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['address']['label'] == '62B Rue de Lille (Paris)'
    assert resp['blocks'][0]['type'] == 'opening_hours'
    assert resp['blocks'][1]['type'] == 'phone'
    assert resp['blocks'][0]['is_24_7'] == False

def test_lang(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{orsay_museum}?lang=it',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:way:63178753'
    assert resp['name'] == "Museo d'Orsay"
    assert resp['local_name'] == "Musée d'Orsay"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['address']['label'] == '62B Rue de Lille (Paris)'
    assert resp['blocks'][0]['type'] == 'opening_hours'
    assert resp['blocks'][1]['type'] == 'phone'
    assert resp['blocks'][0]['is_24_7'] == False

def test_block_null(blancs_manteaux):
    """
    The query corresponding to POI id 'osm:way:55984117' doesn't contain any 'opening_hour' block (the block is null).
    We check the API answer is ok (status_code == 200) with the correct fields.
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{blancs_manteaux}',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:way:55984117'
    assert resp['name'] == "Église Notre-Dame-des-Blancs-Manteaux"
    assert resp['local_name'] == "Église Notre-Dame-des-Blancs-Manteaux"
    assert resp['class_name'] == 'place_of_worship'
    assert resp['subclass_name'] == 'place_of_worship'
    assert resp['address']['label'] == 'Rue Aubriot (Paris)'
    assert resp['blocks'][0]['type'] == 'phone'
    assert resp['blocks'][0]['url'] == 'tel:+33 1 42 72 09 37'


def test_unknow_poi(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/an_unknown_poi_id',
    )

    assert response.status_code == 404
    assert response.json() == {
        "message": "poi 'an_unknown_poi_id' not found"
    }


# Because of the list of block classes, the schema request bugs
# TODO: test schema when the bug will be solved
#
# def test_schema():
#    client = TestClient(app)
#    response = client.get(url='http://localhost/schema')
#
#    assert response.status_code == 200  # for the moment we check just that the schema is not empty
