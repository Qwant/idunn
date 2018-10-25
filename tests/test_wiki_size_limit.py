from apistar.test import TestClient
from app import app
import responses
import pytest

from .test_api import load_poi

@pytest.fixture(autouse=True)
def louvre_museum(mimir_client):
    """
    fill elasticsearch with a fake POI that contains all information possible
    in order that Idunn returns all possible blocks.
    """
    load_poi('louvre_museum.json', mimir_client)


@pytest.fixture(scope='module', autouse=True)
def mock_long_wikipedia_response():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            'https://fr.wikipedia.org/w/api.php',
            json={
                "query": {
                    "pages": [{
                        "pageid": 69682,
                        "ns": 0,
                        "title": "Musée du Louvre",
                        "langlinks": [{"lang": "es", "title": "Museo del Louvre"}]
                    }]
                }
            }
        )

        rsps.add(
            responses.GET,
            'https://es.wikipedia.org/api/rest_v1/page/summary/Museo%20del%20Louvre',
            json={  # This is a subset of the real response
                "extract": "El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia ..."
            }
        )
        yield


def test_wiki_size_limit():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/osm:relation:7515426?lang=es',
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp['blocks'][2].get('blocks')[0].get('description') == 'El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del Louvre es el museo nacional de Francia El Museo del ...'
