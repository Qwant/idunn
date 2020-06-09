import re
import pytest
from unittest.mock import ANY
from fastapi.testclient import TestClient

from app import app
from .utils import enable_pj_source, override_settings, read_fixture


BASE_URL = "http://qwant.bragi"
NLU_URL = "http://qwant.nlu/"
CLASSIF_URL = "http://qwant.classif"
ES_URL = "http://qwant.es"


FIXTURE_AUTOCOMPLETE = read_fixture("fixtures/autocomplete/pavillon_paris.json")
FIXTURE_AUTOCOMPLETE_PARIS = read_fixture("fixtures/autocomplete/paris.json")
FIXTURE_CLASSIF_pharmacy = read_fixture("fixtures/autocomplete/classif_pharmacy.json")
FIXTURE_TOKENIZER = {
    dataset: read_fixture(f"fixtures/autocomplete/nlu/{dataset}.json")
    for dataset in ["with_brand", "with_brand_and_country", "with_cat", "with_country", "with_poi"]
}


def mock_NLU_for(httpx_mock, dataset):
    with override_settings(
        {"NLU_TAGGER_URL": NLU_URL, "NLU_CLASSIFIER_URL": CLASSIF_URL, "PJ_ES": ES_URL}
    ):
        httpx_mock.post(NLU_URL, content=FIXTURE_TOKENIZER[dataset])
        httpx_mock.post(CLASSIF_URL, content=FIXTURE_CLASSIF_pharmacy)
        yield


@pytest.fixture
def mock_NLU_with_brand(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_brand")


@pytest.fixture
def mock_NLU_with_brand_and_country(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_brand_and_country")


@pytest.fixture
def mock_NLU_with_brand_and_country(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_brand_and_country")


@pytest.fixture
def mock_NLU_with_cat(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_cat")


@pytest.fixture
def mock_NLU_with_country(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_country")


@pytest.fixture
def mock_NLU_with_poi(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_poi")


@pytest.fixture
def mock_autocomplete_get(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.get(
            re.compile(f"^{BASE_URL}/autocomplete.*q=paris.*"), content=FIXTURE_AUTOCOMPLETE_PARIS,
        )
        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete"), content=FIXTURE_AUTOCOMPLETE)
        yield


@pytest.fixture
def mock_autocomplete_post(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.post(re.compile(f"^{BASE_URL}/autocomplete"), content=FIXTURE_AUTOCOMPLETE)
        yield


@pytest.fixture
def mock_autocomplete_unavailable(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete"), status_code=502)
        yield


def assert_ok_with(
    client, params, extra=None, expected_intention=None, expected_intention_place=None
):
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


@enable_pj_source()
def test_autocomplete_with_nlu_brand_and_country(
    mock_autocomplete_get, mock_NLU_with_brand_and_country
):
    client = TestClient(app)
    assert_ok_with(
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


@enable_pj_source()
def test_autocomplete_with_nlu_brand_no_focus(mock_autocomplete_get, mock_NLU_with_brand):
    client = TestClient(app)
    assert_ok_with(
        client,
        params={"q": "auchan", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[{"filter": {"q": "auchan"}, "description": {"query": "auchan"}}],
        expected_intention_place=None,
    )


@enable_pj_source()
def test_autocomplete_with_nlu_brand_focus(mock_autocomplete_get, mock_NLU_with_brand):
    client = TestClient(app)
    assert_ok_with(
        client,
        params={"q": "auchan", "lang": "fr", "limit": 7, "nlu": True, "lat": 48.9, "lon": 2.3},
        expected_intention=[{"filter": {"q": "auchan"}, "description": {"query": "auchan"},}],
        expected_intention_place=None,
    )


def test_autocomplete_with_nlu_cat(mock_autocomplete_get, mock_NLU_with_cat):
    client = TestClient(app)
    assert_ok_with(
        client,
        params={"q": "pharmacie", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[
            {"filter": {"category": "pharmacy"}, "description": {"category": "pharmacy"}}
        ],
        expected_intention_place=None,
    )


def test_autocomplete_with_nlu_country(mock_autocomplete_get, mock_NLU_with_country):
    client = TestClient(app)
    assert_ok_with(
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
    assert_ok_with(
        client,
        params={"q": "pharmacie à paris", "lang": "fr", "limit": 7, "nlu": True},
        expected_intention=[],
    )
