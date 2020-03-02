import os
import re
import pytest
import json
from unittest.mock import ANY
import respx
from starlette.testclient import TestClient

from app import app
from .utils import override_settings


BASE_URL = "http://qwant.bragi"
NLU_URL = "http://qwant.nlu/"
CLASSIF_URL = "http://qwant.classif"


def read_fixture(sPath):
    return json.load(open(os.path.join(os.path.dirname(__file__), sPath)))


FIXTURE_AUTOCOMPLETE = read_fixture("fixtures/autocomplete/pavillon_paris.json")
FIXTURE_AUTOCOMPLETE_PARIS = read_fixture("fixtures/autocomplete/paris.json")
FIXTURE_TOKENIZER = read_fixture("fixtures/autocomplete/nlu.json")
FIXTURE_CLASSIF_pharmacy = read_fixture("fixtures/autocomplete/classif_pharmacy.json")


@pytest.fixture
def mocked_responses():
    with respx.mock as rsps:
        yield rsps


@pytest.fixture
def mock_NLU(mocked_responses):
    with override_settings({"NLU_TOKENIZER_URL": NLU_URL, "NLU_CLASSIFIER_URL": CLASSIF_URL}):
        respx.post(
            NLU_URL,
            content=FIXTURE_TOKENIZER,
        )
        respx.post(
            CLASSIF_URL,
            content=FIXTURE_CLASSIF_pharmacy
        )
        yield mocked_responses


@pytest.fixture
def mock_autocomplete_get(mocked_responses):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        respx.get(
            re.compile(f"^{BASE_URL}/autocomplete.*q=paris.*"),
            content=FIXTURE_AUTOCOMPLETE_PARIS,
        )
        respx.get(
            re.compile(f"^{BASE_URL}/autocomplete"),
            content=FIXTURE_AUTOCOMPLETE,
        )
        yield mocked_responses


@pytest.fixture
def mock_autocomplete_post(mocked_responses):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        respx.post(
            re.compile(f"^{BASE_URL}/autocomplete"),
            content=FIXTURE_AUTOCOMPLETE,
        )
        yield mocked_responses


@pytest.fixture
def mock_autocomplete_unavailable(mocked_responses):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        respx.get(
            re.compile(f"^{BASE_URL}/autocomplete"),
            status_code=502
        )
        yield mocked_responses


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

    if "nlu" in params:
        intentions = data["intentions"]
        assert intentions == [
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
        ]
        assert (
            intentions[0]["description"]["place"]["properties"]["geocoding"]["label"]
            == "Paris (75000-75116), Île-de-France, France"
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


def test_autocomplete_with_nlu(mock_autocomplete_get, mock_NLU):
    client = TestClient(app)
    assert_ok_with(client, params={"q": "pharmacie à paris", "lang": "fr", "limit": 7, "nlu": True})
