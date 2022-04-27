# pylint: disable = redefined-outer-name, unused-argument, unused-import

import pytest
from fastapi.testclient import TestClient
from app import app

from ..fixtures.geocodeur.autocomplete import (
    mock_autocomplete_get,
    mock_NLU_with_cat,
    mock_NLU_with_city,
    mock_NLU_with_category_and_city,
    mock_NLU_with_brand_and_city,
    mock_NLU_with_picasso,
    mock_NLU_with_moliere,
    mock_NLU_with_chez_eric,
    mock_bragi_carrefour_in_bbox,
)

from ..fixtures.geocodeur.search import (
    mock_search_get,
)

from ..fixtures.api.pj import mock_pj_api_find_with_musee_picasso, mock_pj_api_find_with_chez_eric


def test_ia_paris(mock_search_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 1
    place = places[0]
    assert place["name"] == "Paris"


def test_ia_item_not_found_in_db(mock_search_get, mock_NLU_with_city):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "pavillon paris", "lang": "fr"})
    assert response.status_code == 204


def test_ia_paris_with_region(mock_search_get, mock_NLU_with_city):
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


def test_ia_paris_request_international(mock_search_get, mock_NLU_with_city):
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


def test_ia_category_intention_tripadvisor_source(
    mock_NLU_with_category_and_city, mock_autocomplete_get
):
    client = TestClient(app)
    response = client.get("/v1/instant_answer", params={"q": "hotel à paris", "lang": "fr"})
    assert response.status_code == 200
    response_json = response.json()
    places = response_json["data"]["result"]["places"]
    assert len(places) == 2
    place = places[0]
    assert place["name"] == "Bergrestaurant Suecka"
    source = response_json["data"]["result"]["source"]
    assert source == "tripadvisor"


def test_ia_brand_intention_full_text(
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


def test_ia_brand_intention_full_text_with_region(
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
def test_ia_brand_intention_single_result(
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
    assert response.status_code == 204


# should mock differently tripadvisor search call
# def test_ia_addresses_ranking(mock_search_get, mock_autocomplete_get):
#     client = TestClient(app)
#     response = client.get("/v1/instant_answer", params={"q": "43 rue de paris rennes"})
#     assert response.status_code == 200
#     places = response.json()["data"]["result"]["places"]
#     assert len(places) == 1
#     assert places[0]["name"] == "43 Rue de Paris"
