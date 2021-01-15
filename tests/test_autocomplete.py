# pylint: disable = redefined-outer-name, unused-argument, unused-import

from unittest.mock import ANY
from fastapi.testclient import TestClient

from app import app
from .fixtures.autocomplete import (
    mock_autocomplete_get,
    mock_autocomplete_post,
    mock_autocomplete_unavailable,
    mock_NLU_with_poi,
    mock_NLU_with_brand,
    mock_NLU_with_cat,
    mock_NLU_with_cat_city_country,
    mock_NLU_with_brand_and_city,
)


def assert_ok_with(client, params, extra=None):
    url = "http://localhost/v1/autocomplete"

    if extra is None:
        response = client.get(url, params=params)
    else:
        response = client.post(url, params=params, json=extra)

    data = response.json()

    assert response.status_code == 200

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert feature["geometry"]["type"] == "Point"

    properties = feature["properties"]["geocoding"]
    assert properties["type"] == "poi"
    assert properties["name"] == "pavillon Eiffel"
    assert properties["label"] == "pavillon Eiffel (Paris)"
    assert properties["address"]["label"] == "5 Avenue Anatole France (Paris)"


def assert_intention(client, params, expected_intention=None, expected_intention_place=None):
    url = "http://localhost/v1/autocomplete"
    response = client.get(url, params=params)

    data = response.json()
    assert response.status_code == 200
    assert len(data.get("features")) > 0
    intentions = data.get("intentions", None)
    assert intentions == expected_intention

    if intentions:
        if expected_intention_place is None:
            assert intentions[0]["description"].get("place") is None
        else:
            assert (
                intentions[0]["description"]["place"]["properties"]["geocoding"]["label"]
                == expected_intention_place
            )


def test_autocomplete_ok(mock_autocomplete_get):
    client = TestClient(app)
    assert_ok_with(client, params={"q": "pavillon paris", "lang": "en", "limit": 7})


def test_autocomplete_ok_defaults(mock_autocomplete_get):
    client = TestClient(app)
    assert_ok_with(client, params={"q": "pavillon paris"})


def test_autocomplete_ok_shape(mock_autocomplete_post):
    client = TestClient(app)
    assert_ok_with(
        client,
        params={"q": "paris", "lang": "en", "limit": 7},
        extra={
            "shape": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[2.29, 48.78], [2.34, 48.78], [2.34, 48.81], [2.29, 48.81], [2.29, 48.78]]
                    ],
                },
            }
        },
    )


def test_autocomplete_unavailable(mock_autocomplete_unavailable):
    client = TestClient(app)
    resp = client.get("http://localhost/v1/autocomplete", params={"q": "paris"})
    assert resp.status_code == 503


def test_autocomplete_with_nlu_brand_and_city(mock_autocomplete_get, mock_NLU_with_brand_and_city):
    client = TestClient(app)
    assert_intention(
        client,
        params={"q": "auchan à paris", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[
            {
                "filter": {"q": "auchan", "bbox": [2.224122, 48.8155755, 2.4697602, 48.902156]},
                "description": {
                    "query": "auchan",
                    "place": {"type": "Feature", "geometry": ANY, "properties": ANY},
                },
            }
        ],
        expected_intention_place="Paris (75000-75116), Île-de-France, France",
    )


def test_autocomplete_with_nlu_brand_no_focus(mock_autocomplete_get, mock_NLU_with_brand):
    client = TestClient(app)
    assert_intention(
        client,
        params={"q": "auchan", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[{"filter": {"q": "auchan"}, "description": {"query": "auchan"}}],
        expected_intention_place=None,
    )


def test_autocomplete_with_nlu_brand_focus(mock_autocomplete_get, mock_NLU_with_brand):
    client = TestClient(app)
    assert_intention(
        client,
        params={"q": "auchan", "lang": "fr", "limit": 7, "nlu": True, "lat": 48.9, "lon": 2.3},
        expected_intention=[{"filter": {"q": "auchan"}, "description": {"query": "auchan"},}],
        expected_intention_place=None,
    )


def test_autocomplete_with_nlu_cat(mock_autocomplete_get, mock_NLU_with_cat):
    client = TestClient(app)
    assert_intention(
        client,
        params={"q": "pharmacie", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[
            {"filter": {"category": "pharmacy"}, "description": {"category": "pharmacy"}}
        ],
        expected_intention_place=None,
    )


def test_autocomplete_with_nlu_country(mock_autocomplete_get, mock_NLU_with_cat_city_country):
    client = TestClient(app)
    assert_intention(
        client,
        params={"q": "pharmacie à paris, france", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[
            {
                "filter": {
                    "category": "pharmacy",
                    "bbox": [2.224122, 48.8155755, 2.4697602, 48.902156],
                },
                "description": {
                    "category": "pharmacy",
                    "place": {"type": "Feature", "geometry": ANY, "properties": ANY},
                },
            }
        ],
        expected_intention_place="Paris (75000-75116), Île-de-France, France",
    )


def test_autocomplete_with_nlu_poi(mock_autocomplete_get, mock_NLU_with_poi):
    client = TestClient(app)
    assert_intention(
        client,
        params={"q": mock_NLU_with_poi["text"], "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[],
    )


def test_no_intention_for_brand_with_no_matching_feature(
    mock_autocomplete_get, mock_NLU_with_brand
):
    client = TestClient(app)
    brand_query = mock_NLU_with_brand["text"]
    assert brand_query == "auchan"

    assert_intention(
        client,
        params={"q": "this is not a brand", "lang": "fr", "limit": 7, "nlu": True,},
        expected_intention=[],
    )
