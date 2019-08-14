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
    with override_settings(
        {"QWANT_DIRECTIONS_API_BASE_URL": "http://api.qwant/directions"}
    ):
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
            "combigo_directions_publictransport.json",
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
        params={"language": "fr", "type": "car"},
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
    assert list(map(
        lambda part: part['mode'],
        response_data['data']['routes'][0]['summary']
    )) == ['WALK', 'SUBWAY', 'WALK', 'SUBWAY', 'WALK']
