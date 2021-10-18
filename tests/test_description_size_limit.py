from fastapi.testclient import TestClient
from app import app
import responses
import pytest

from .utils import override_settings


@pytest.fixture(scope="function")
def wiki_max_size():
    with override_settings({"DESC_MAX_SIZE": 10}):
        yield


@pytest.fixture(scope="module", autouse=True)
def mock_long_wikipedia_response():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://fr.wikipedia.org/w/api.php",
            json={
                "query": {
                    "pages": [
                        {
                            "pageid": 69682,
                            "ns": 0,
                            "title": "Musée du Louvre",
                            "langlinks": [{"lang": "es", "title": "Museo del Louvre"}],
                        }
                    ]
                }
            },
        )

        rsps.add(
            responses.GET,
            "https://es.wikipedia.org/api/rest_v1/page/summary/Museo%20del%20Louvre",
            json={"extract": "El Museo del Louvre es el museo nacional de Francia " * 25},
        )
        yield


def test_description_size_limit(wiki_max_size):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    resp = response.json()

    # Test that the wiki block description string is not longer than
    # DESC_MAX_SIZE (here only 10 chars).
    assert resp["blocks"][4]["description"] == "El Museo d…"
