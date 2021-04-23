import pytest
from fastapi.testclient import TestClient
from app import app

from .fixtures.autocomplete import (
    mock_autocomplete_get,
    mock_NLU_with_city,
    mock_NLU_with_brand_and_city,
    mock_bragi_carrefour_in_bbox,
)


def test_search_paris(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    place = response_json["place"]
    assert place["name"] == "Paris"


def test_search_intention_full_text(
    mock_NLU_with_brand_and_city, mock_autocomplete_get, mock_bragi_carrefour_in_bbox
):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "carrefour à paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    places = response_json["bbox_places"]["places"]
    assert len(places) == 5
    place = places[0]
    assert place["name"] == "Carrefour Market"


@pytest.mark.parametrize("mock_bragi_carrefour_in_bbox", [{"limit": 1}], indirect=True)
def test_search_intention_single_result(
    mock_NLU_with_brand_and_city, mock_autocomplete_get, mock_bragi_carrefour_in_bbox
):
    client = TestClient(app)
    response = client.get("/v1/search", params={"q": "carrefour à paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    place = response_json["place"]
    assert place["name"] == "Carrefour Market"
