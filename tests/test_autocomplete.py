import json
import os
import re
from urllib.parse import parse_qs, urlparse

import pytest
import responses
from starlette.testclient import TestClient

from app import app
from .utils import override_settings


BASE_URL = "http://qwant.bragi"
NLU_URL = "http://qwant.nlu/"
CLASSIF_URL = "http://qwant.classif"


def path_from_string(sPath):
    return os.path.join(os.path.dirname(__file__), sPath)


FIXTURE_PATH = path_from_string("fixtures/autocomplete/paris.json")
FIXTURE_PATH_NLU = path_from_string("fixtures/autocomplete/nlu.json")
FIXTURE_PATH_CLASSIF_pharmacy = path_from_string("fixtures/autocomplete/classif_pharmacy.json")
FIXTURE_PATH_CLASSIF_paris = path_from_string("fixtures/autocomplete/classif_paris.json")


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_NLU(mocked_responses):
    with override_settings(
        {"AUTOCOMPLETE_NLU_URL": NLU_URL, "AUTOCOMPLETE_CLASSIFIER_URL": CLASSIF_URL}
    ):
        mocked_responses.add(
            responses.POST, f"{NLU_URL}", body=open(FIXTURE_PATH_NLU).read(), status=200,
        )
        """
        Two queries to the classifier API are required here,
        as a consequence the order of the two queries below is important
        """
        mocked_responses.add(
            responses.POST,
            f"{CLASSIF_URL}",
            body=open(FIXTURE_PATH_CLASSIF_pharmacy).read(),
            status=200,
        )
        mocked_responses.add(
            responses.POST,
            f"{CLASSIF_URL}",
            body=open(FIXTURE_PATH_CLASSIF_paris).read(),
            status=200,
        )
        yield mocked_responses


@pytest.fixture
def mock_autocomplete_get(mocked_responses):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        mocked_responses.add(
            responses.GET,
            re.compile(f"^{BASE_URL}/autocomplete"),
            body=open(FIXTURE_PATH).read(),
            status=200,
        )
        yield mocked_responses


@pytest.fixture
def mock_autocomplete_post():
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        with responses.RequestsMock() as resps:
            resps.add(
                responses.POST,
                re.compile(f"^{BASE_URL}/autocomplete"),
                body=open(FIXTURE_PATH).read(),
                status=200,
            )
            yield


@pytest.fixture
def mock_autocomplete_unavailable():
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        with responses.RequestsMock() as resps:
            resps.add(responses.GET, re.compile(f"^{BASE_URL}/autocomplete"), status=502)
            yield


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
        assert len(intentions) == 2
        assert intentions[0]["intention"] == "pharmacy"
        assert intentions[1]["intention"] == "restaurant"


def test_autocomplete_ok(mock_autocomplete_get):
    client = TestClient(app)
    assert_ok_with(client, params={"q": "paris", "lang": "en", "limit": 7})


def test_autocomplete_ok_defaults(mock_autocomplete_get):
    client = TestClient(app)
    assert_ok_with(client, params={"q": "paris"})


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
    assert_ok_with(client, params={"q": "pharmacy paris", "lang": "en", "limit": 7, "nlu": True})
