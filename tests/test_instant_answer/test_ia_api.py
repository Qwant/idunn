# pylint: disable = redefined-outer-name, unused-argument, unused-import

import pytest
from fastapi.testclient import TestClient
from app import app

from ..fixtures.autocomplete import (
    mock_autocomplete_get,
    mock_NLU_with_city,
    mock_NLU_with_brand_and_city,
    mock_bragi_carrefour_in_bbox,
)


def test_ia_paris(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 1
    place = places[0]
    assert place["name"] == "Paris"


def test_ia_paris_with_region(mock_autocomplete_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get(
        "/v1/instant_answer",
        params={"q": "paris", "lang": "fr", "user_region": "fr"},
    )
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 1
    place = places[0]
    assert place["name"] == "Paris"


def test_ia_paris_request_international(mock_autocomplete_get, mock_NLU_with_city):
    """
    The user queries for the name in Italian while lang = "fr".
    """
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "parigi", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 1
    place = places[0]
    assert place["name"] == "Paris"


def test_ia_intention_full_text(
    mock_NLU_with_brand_and_city, mock_autocomplete_get, mock_bragi_carrefour_in_bbox
):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "carrefour à paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 5
    place = places[0]
    assert place["name"] == "Carrefour Market"


def test_ia_intention_full_text_with_region(
    mock_NLU_with_brand_and_city, mock_autocomplete_get, mock_bragi_carrefour_in_bbox
):
    client = TestClient(app)
    response = client.get(
        "/v1/instant_answer",
        params={"q": "carrefour à paris", "lang": "fr", "user_region": "fr"},
    )
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 5
    place = places[0]
    assert place["name"] == "Carrefour Market"


@pytest.mark.parametrize("mock_bragi_carrefour_in_bbox", [{"limit": 1}], indirect=True)
def test_ia_intention_single_result(
    mock_NLU_with_brand_and_city, mock_autocomplete_get, mock_bragi_carrefour_in_bbox
):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "carrefour à paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 1
    place = places[0]
    assert place["name"] == "Carrefour Market"


def test_ia_query_too_long():
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "A" * 101})
    assert response.status_code == 404
