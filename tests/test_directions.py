import os
import json
import responses
import re
import pytest
from apistar.test import TestClient
from app import app

from .utils import override_settings


@pytest.fixture
def mock_directions_car():
    with override_settings({
        "QWANT_DIRECTIONS_API_BASE_URL": "http://api.qwant/directions",
        "MAPBOX_DIRECTIONS_ACCESS_TOKEN": None,
    }):
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures/directions",
            "qwant_directions_car.json",
        )
        with responses.RequestsMock() as rsps:
            rsps.add(
                "GET",
                re.compile(r"^http://api.qwant/directions/"),
                status=200,
                json=json.load(open(fixture_path)),
            )
            yield


@pytest.fixture
def mock_directions_public_transport():
    with override_settings({"COMBIGO_API_BASE_URL": "http://api.test"}):
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures/directions",
            "combigo_v1_publictransport.json",
        )
        with responses.RequestsMock() as rsps:
            rsps.add(
                "GET",
                re.compile(r"^http://api.test/journey/"),
                status=200,
                json=json.load(open(fixture_path)),
            )
            yield


def test_direction_car(mock_directions_car):
    client = TestClient(app)
    response = client.get(
        "http://localhost/v1/directions/"
        "2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={"language": "fr", "type": "driving"},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data['status'] == 'success'
    assert len(response_data['data']['routes']) == 3
    assert all(r['geometry'] for r in response_data['data']['routes'])
    assert response_data['data']['routes'][0]['duration'] == 1819
    assert len(response_data['data']['routes'][0]['legs']) == 1
    assert len(response_data['data']['routes'][0]['legs'][0]['steps']) == 10


def test_direction_public_transport(mock_directions_public_transport):
    client = TestClient(app)
    response = client.get(
        "http://localhost/v1/directions/"
        "2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={"language": "fr", "type": "publictransport"},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data['status'] == 'success'
    assert len(response_data['data']['routes']) == 3
    assert all(r['geometry'] for r in response_data['data']['routes'])

    route = response_data['data']['routes'][0]
    geometry = route['geometry']
    assert geometry['type'] == 'FeatureCollection'
    assert geometry['features'][1]['properties'] == {
        'direction': "Mairie d'Issy (Issy-les-Moulineaux)",
        'lineColor': '007852',
        'mode': 'SUBWAY',
        'num': '12',
        'network': 'METRO'
    }

    summary= route['summary']
    assert list(map(
        lambda part: part['mode'],
        summary
    )) == ['WALK', 'SUBWAY', 'WALK', 'SUBWAY', 'WALK']

    # Walk summary
    assert summary[0]['info'] is None
    assert summary[0]['distance'] > 0
    assert summary[0]['duration'] > 0

    # Subway summary
    assert summary[1]['info']['num'] == '12'
    assert summary[1]['info']['direction'] == "Mairie d'Issy (Issy-les-Moulineaux)"
    assert summary[1]['info']['lineColor'] == "007852"
    assert summary[1]['info']['network'] == "METRO"


def test_directions_not_configured():
    with override_settings({
        "QWANT_DIRECTIONS_API_BASE_URL": None,
        "MAPBOX_DIRECTIONS_ACCESS_TOKEN": None,
    }):
        client = TestClient(app)
        response = client.get(
            "http://localhost/v1/directions/"
            "2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
            params={"language": "fr", "type": "driving"},
        )
        assert response.status_code == 501
