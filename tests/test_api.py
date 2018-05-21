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
    # we load the poi in 'munin_poi' even if in reality mimir load it in another index and alias in to 'munin_poi'
    es_client.indices.create(index='munin_poi')
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
        url=f'http://localhost/v1/poi/{orsay_museum}',
        params={'lang': 'fr'}
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "osm:node:2379542204",
        "label": "Musée d'Orsay (Paris)",
        "name": "Musée d'Orsay"
    }



def test_schema():
    client = TestClient(app)
    response = client.get(url='http://localhost/schema')

    assert response.status_code == 200  # for the moment we check just that the schema is not empty
