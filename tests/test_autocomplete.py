import json
import os
import re
from urllib.parse import parse_qs, urlparse

import pytest
import responses
from starlette.testclient import TestClient

from app import app
from .utils import override_settings


BASE_URL = 'http://qwant.bragi'

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__),
    'fixtures/autocomplete/paris.json'
)


@pytest.fixture
def mock_autocomplete_get():
    with override_settings({'BRAGI_BASE_URL': BASE_URL}):
        with responses.RequestsMock() as resps:
            resps.add(
                responses.GET,
                re.compile(f'^{BASE_URL}/autocomplete'),
                body=open(FIXTURE_PATH).read(),
                status=200,
            )
            yield


@pytest.fixture
def mock_autocomplete_post():
    with override_settings({'BRAGI_BASE_URL': BASE_URL}):
        with responses.RequestsMock() as resps:
            resps.add(
                responses.POST,
                re.compile(f'^{BASE_URL}/autocomplete'),
                body=open(FIXTURE_PATH).read(),
                status=200,
            )
            yield


@pytest.fixture
def mock_autocomplete_unavailable():
    with override_settings({'BRAGI_BASE_URL': BASE_URL}):
        with responses.RequestsMock() as resps:
            resps.add(
                responses.GET,
                re.compile(f'^{BASE_URL}/autocomplete'),
                status=502,
            )
            yield



def assert_ok_with(client, params, extra=None):
    url = 'http://localhost/v1/autocomplete'

    if extra is None:
        response = client.get(url, params=params)
    else:
        response = client.post(url, params=params, json=extra)

    data = response.json()

    assert response.status_code == 200

    feature = data['features'][0]
    assert feature['type'] == 'Feature'
    assert len(feature['geometry']['coordinates']) == 2
    assert feature['geometry']['type'] == 'Point'

    properties = feature['properties']['geocoding']
    assert properties['type'] == 'poi'
    assert properties['name'] == 'pavillon Eiffel'
    assert properties['label'] == 'pavillon Eiffel (Paris)'
    assert properties['address']['label'] == '5 Avenue Anatole France (Paris)'


def test_autocomplete_ok(mock_autocomplete_get):
    client = TestClient(app)
    assert_ok_with(client, params={'q': 'paris', 'lang': 'en', 'limit': 7})


def test_autocomplete_ok_defaults(mock_autocomplete_get):
    client = TestClient(app)
    assert_ok_with(client, params={'q': 'paris'})


def test_autocomplete_ok_shape(mock_autocomplete_post):
    client = TestClient(app)
    assert_ok_with(
        client,
        params={'q': 'paris', 'lang': 'en', 'limit': 7},
        extra={
            'shape': {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [2.29, 48.78],
                        [2.34, 48.78],
                        [2.34, 48.81],
                        [2.29, 48.81],
                        [2.29, 48.78],
                    ]]
                }
            }
        }
    )

def test_autocomplete_unavailable(mock_autocomplete_unavailable):
    client = TestClient(app)
    resp = client.get('http://localhost/v1/autocomplete', params={'q': 'paris'})
    assert resp.status_code == 500
