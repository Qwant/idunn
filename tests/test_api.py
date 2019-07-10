from app import app
from apistar.test import TestClient

def test_basic_query():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/osm:way:63178753?lang=fr',
    )

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'

    resp = response.json()

    assert resp['id'] == 'osm:way:63178753'
    assert resp['name'] == "Musée d'Orsay"
    assert resp['local_name'] == "Musée d'Orsay"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['address']['label'] == '1 Rue de la Légion d\'Honneur (Paris)'
    assert resp['blocks'][0]['type'] == 'opening_hours'
    assert resp['blocks'][1]['type'] == 'phone'
    assert resp['blocks'][0]['is_24_7'] == False

def test_lang():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/osm:way:63178753?lang=it',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:way:63178753'
    assert resp['name'] == "Museo d'Orsay"
    assert resp['local_name'] == "Musée d'Orsay"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['address']['label'] == '1 Rue de la Légion d\'Honneur (Paris)'
    assert resp['blocks'][0]['type'] == 'opening_hours'
    assert resp['blocks'][1]['type'] == 'phone'
    assert resp['blocks'][0]['is_24_7'] == False

def test_contact_phone():
    """
    The louvre museum has the tag 'contact:phone'
    We test this tag is correct here
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/osm:relation:7515426',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:relation:7515426'
    assert resp['name'] == "Louvre Museum"
    assert resp['local_name'] == "Musée du Louvre"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['blocks'][1]['type'] == 'phone'
    assert resp['blocks'][1]['url'] == 'tel:+33140205229'
    assert resp['blocks'][1]['international_format'] == '+33 1 40 20 52 29'
    assert resp['blocks'][1]['local_format'] == '01 40 20 52 29'

def test_block_null():
    """
    The query corresponding to POI id 'osm:way:55984117' doesn't contain any 'opening_hour' block (the block is null).
    We check the API answer is ok (status_code == 200) with the correct fields.
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/osm:way:55984117?lang=fr',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['id'] == 'osm:way:55984117'
    assert resp['name'] == "Église Notre-Dame-des-Blancs-Manteaux"
    assert resp['local_name'] == "Église Notre-Dame-des-Blancs-Manteaux"
    assert resp['class_name'] == 'place_of_worship'
    assert resp['subclass_name'] == 'place_of_worship'
    assert resp['blocks'][0]['type'] == 'phone'
    assert resp['address']['label'] == 'Rue Aubriot (Paris)'
    assert resp['blocks'][0]['url'] == 'tel:+33142720937'


def test_unknow_poi():
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

def test_services_and_information():
    """
    Test that the services_and_information block
    contains the 3 correct blocks (accessibility,
    internet_access, brewery).
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/osm:way:63178753?lang=fr',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp.get('blocks')[2].get('blocks')[0].get('blocks') == [
	{
	    "type": "accessibility",
	    "wheelchair": "yes",
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

def test_exc_scenario():
    """
    A scenario with 2 consecutive requests that used to cause unhandled errors
    because of a bug in Apistar injector.
    """
    client = TestClient(app)
    response = client.get('http://localhost/v1/places?bbox=-0.3,49.2,8.1,55.5&size=52&category=bar&lang=fr')
    assert response.status_code == 400
    response = client.get('http://localhost/v1/abcdef')
    assert response.status_code == 404
