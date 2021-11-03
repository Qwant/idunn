import pytest
from fastapi.testclient import TestClient
from app import app

from .fixtures.autocomplete import (
    mock_autocomplete_get,
    mock_NLU_with_city,
    mock_NLU_with_brand_and_city,
)


def test_empty_search(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "", "lang": "fr", "nlu": True})
    assert response.status_code == 204


def test_search_qwant_maps(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "qwant maps", "lang": "fr", "nlu": True})
    assert response.status_code == 204


def test_search_paris(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "paris", "lang": "fr", "nlu": True})
    assert response.status_code == 200
    response_json = response.json()
    place = response_json["features"][0]["properties"]["geocoding"]
    assert response_json["geocoding"]["query"] == "paris"
    assert place["name"] == "Paris"


def test_search_intention_full_text(mock_NLU_with_brand_and_city, mock_autocomplete_get):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "auchan à paris", "lang": "fr", "nlu": True})
    assert response.status_code == 200
    response_json = response.json()
    intention = response_json["intentions"][0]["filter"]
    assert response_json["geocoding"]["query"] == "auchan à paris"
    assert intention["q"] == "auchan"
    assert intention["bbox"] is not None
