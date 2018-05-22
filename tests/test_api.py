from apistar.test import TestClient
from app import app
import pytest
import json
import os


@pytest.fixture(scope="module")
def orsay_museum(es_client):
    """
    fill elasticsearch with one poi, the orsay museum
    """
    # we load the poi in 'munin_poi_specific' index and alias it to 'munin_poi' to have a architecture like mimir
    index_name = 'munin_poi_specific'
    es_client.indices.create(index=index_name)
    es_client.indices.put_alias(name='munin_poi', index=index_name)
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'orsay_museum.json')
    with open(filepath, "r") as f:
        orsay_museum = json.load(f)
        poi_id = orsay_museum['id']
        es_client.index(index='munin_poi',
                        body=orsay_museum,
                        doc_type='poi',
                        id=poi_id,
                        refresh=True)
        return poi_id


def test_basic_query(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{orsay_museum}',
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "osm:way:63178753",
        "label": "Musée d'Orsay (Paris)",
        "name": "Musée d'Orsay"
    }


def test_unknow_poi(orsay_museum):
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/an_unknown_poi_id',
    )

    assert response.status_code == 404
    assert response.json() == {
        "message": "poi 'an_unknown_poi_id' not found"
    }


def test_schema():
    client = TestClient(app)
    response = client.get(url='http://localhost/schema')

    assert response.status_code == 200  # for the moment we check just that the schema is not empty
