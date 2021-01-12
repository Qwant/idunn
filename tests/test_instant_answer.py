from fastapi.testclient import TestClient

from app import app
from .fixtures.autocomplete import mock_autocomplete_get, mock_NLU_with_city


def test_ia_paris(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json["places"]) == 1
    place = response_json["places"][0]
    assert place["name"] == "Paris"
