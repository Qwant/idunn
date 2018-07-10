from apistar.test import TestClient
from app import app
import pytest
import json
import os


def load_poi(file_name, mimir_client):
    """
    Load a json file in the elasticsearch and returns the corresponding POI id
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', file_name)
    with open(filepath, "r") as f:
        poi = json.load(f)
        poi_id = poi['id']
        mimir_client.index(index='munin_poi',
                        body=poi,
                        doc_type='poi',
                        id=poi_id,
                        refresh=True)
        return poi_id

@pytest.fixture(scope="session")
def orsay_museum(mimir_client, init_indices):
    """
    fill elasticsearch with the orsay museum
    """
    return load_poi('orsay_museum.json', mimir_client)

@pytest.fixture(scope="session")
def blancs_manteaux(mimir_client, init_indices):
    """
    fill elasticsearch with the church des blancs manteaux
    """
    return load_poi('blancs_manteaux.json', mimir_client)

@pytest.fixture(scope="session")
def louvre_museum(init_indices, mimir_client):
    """
    fill elasticsearch with the louvre museum (with the tag 'contact:phone')
    """
    return load_poi('louvre_museum.json', mimir_client)

def test_basic_query(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{orsay_museum}?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

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

def test_contact_phone(louvre_museum):
    """
    The louvre museum has the tag 'contact:phone'
    We test this tag is correct here
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{louvre_museum}',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:relation:7515426'
    assert resp['name'] == "Louvre Museum"
    assert resp['local_name'] == "Musée du Louvre"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['blocks'][1]['type'] == 'phone'
    assert resp['blocks'][1]['url'] == 'tel:+33 1 40 20 52 29'

def test_block_null(blancs_manteaux):
    """
    The query corresponding to POI id 'osm:way:55984117' doesn't contain any 'opening_hour' block (the block is null).
    We check the API answer is ok (status_code == 200) with the correct fields.
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{blancs_manteaux}?lang=fr',
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
        url='http://localhost/v1/pois/an_unknown_poi_id',
    )

    assert response.status_code == 404
    assert response.json() == {
        "message": "poi 'an_unknown_poi_id' not found"
    }

def test_schema():
    client = TestClient(app)
    response = client.get(url='http://localhost/schema')

    assert response.status_code == 200  # for the moment we check just that the schema is not empty

def test_services_and_information(orsay_museum):
    """
    Test that the services_and_information block
    contains the 3 correct blocks (accessibility,
    internet_access, brewery).
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{orsay_museum}?lang=fr',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp.get('blocks')[2].get('blocks')[0].get('blocks') == [
	{
	    "type": "accessibility",
	    "wheelchair": "true",
	    "tactile_paving": "unknown",
	    "toilets_wheelchair": "unknown"
	},
	{
	    "type": "internet_access",
	    "wifi": True
	},
	{
	    "type": "brewery",
	    "beers": [
		{
		    "name": "Tripel Karmeliet"
		},
		{
		    "name": "Delirium"
		},
                {
                    "name": "Chouffe"
                }
	    ]
	}
    ]

