# pylint: disable = redefined-outer-name, unused-argument, unused-import

import pytest
from fastapi.testclient import TestClient
from app import app
from idunn.api.instant_answer import PlaceFilter
from idunn.api.places import PlaceType

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


def test_ia_filters():
    place_filter = PlaceFilter(
        type=PlaceType.ADDRESS, name="5 rue Gustave Zédé", postcodes=["79000"]
    )

    # Case is ignored
    assert place_filter.filter("5 RuE gustave ZÉDÉ")

    # Extra terms are not allowed
    assert not place_filter.filter("5 rue gustave zédé restaurant")

    # Numbers must match
    assert not place_filter.filter("1 rue gustave zédé")
    assert not place_filter.filter("5 rue gustave zédé 75015")

    # Accents can be omitted
    assert place_filter.filter("5 rue gustave zede")

    # Accents in the request still matter
    assert not place_filter.filter("5 rue güstâve zédé")

    # A single spelling mistake is allowed per word
    assert place_filter.filter("5 ruee gustaev zde")
    assert not place_filter.filter("5 rueee gusteav ze")
    assert not place_filter.filter("5 rue gusteav zede")
    assert not place_filter.filter("5 rue gusta zede")

    # Dashes are ignored
    assert place_filter.filter("5 rue gustave--zede")

    # Bis/Ter/... are ignored in the query
    assert place_filter.filter("5 Bis rue gustave zede")
    assert place_filter.filter("5Ter rue gustave zede")

    # Support some abreviations
    assert place_filter.filter("5 r gustave zédé")
    assert not place_filter.filter("5 u gustave zédé")

    # Queries that match a small part of the request are ignored, postcode and
    # admins matter in relevant matching words.
    assert PlaceFilter(
        type=PlaceType.ADMIN, name="2e Arrondissement", admins=["Paris"], postcodes=["75002"]
    ).filter("Paris 2e")
    assert not PlaceFilter(type=PlaceType.ADDRESS, name="101 rue des dalmatiens").filter(
        "101 dalmatiens"
    )
