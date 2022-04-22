import os
import json
import responses
import re
import pytest
from idunn import settings
from idunn.utils import rate_limiter
from fastapi.testclient import TestClient
from app import app
from freezegun import freeze_time
from idunn.utils.redis import get_redis_pool

from tests.test_rate_limiter import disable_redis, limiter_test_normal

from .utils import override_settings


@pytest.fixture
def mock_directions_car():
    with override_settings(
        {
            "QWANT_DIRECTIONS_API_BASE_URL": "http://api.qwant/directions",
            "MAPBOX_DIRECTIONS_ACCESS_TOKEN": None,
        }
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
            yield rsps


@pytest.fixture
def mock_directions_car_with_rate_limiter(redis, mock_directions_car):
    with override_settings({"REDIS_URL": redis}):
        rate_limiter.redis_pool = get_redis_pool(settings["RATE_LIMITER_REDIS_DB"])
        yield

    # reset rate_limiter to default redis connection url
    rate_limiter.redis_pool = None


@pytest.fixture
def mock_directions_public_transport():
    with override_settings({"COMBIGO_API_BASE_URL": "http://api.test"}):
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures/directions",
            "combigo_v1.1_publictransport.json",
        )
        with responses.RequestsMock() as rsps:
            rsps.add(
                "POST",
                re.compile(r"^http://api.test/journey"),
                status=200,
                json=json.load(open(fixture_path)),
            )
            yield rsps


@freeze_time("2018-06-14 8:30:00", tz_offset=0)
def test_direction_car(mock_directions_car):
    client = TestClient(app)
    response = client.get(
        "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={"language": "fr", "type": "driving", "exclude": "ferry"},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["status"] == "success"
    assert len(response_data["data"]["routes"]) == 3
    assert response_data["data"]["routes"][0]["start_time"] == "2018-06-14T10:30:00+02:00"
    assert response_data["data"]["routes"][0]["end_time"] == "2018-06-14T11:00:19+02:00"
    assert all(r["geometry"] for r in response_data["data"]["routes"])
    assert response_data["data"]["routes"][0]["duration"] == 1819
    assert len(response_data["data"]["routes"][0]["legs"]) == 1
    assert len(response_data["data"]["routes"][0]["legs"][0]["steps"]) == 10
    assert response_data["data"]["routes"][0]["legs"][0]["mode"] == "CAR"
    assert "exclude=ferry" in mock_directions_car.calls[0].request.url


def test_direction_car_with_ids(mock_directions_car):
    client = TestClient(app)
    response = client.get(
        "http://localhost/v1/directions",
        params={
            "language": "fr",
            "type": "driving",
            "exclude": "ferry",
            "origin": "latlon:48.89007:2.34023",
            "destination": "osm:way:63178753",
        },
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["status"] == "success"
    assert len(response_data["data"]["routes"]) == 3
    assert response_data["data"]["routes"][0]["legs"][0]["mode"] == "CAR"
    mocked_request_url = mock_directions_car.calls[0].request.url
    assert "exclude=ferry" in mocked_request_url
    assert "2.34023,48.89007;2.32658,48.85992" in mocked_request_url


def test_direction_public_transport(mock_directions_public_transport):
    client = TestClient(app)
    response = client.get(
        "http://localhost/v1/directions/" "2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={"language": "fr", "type": "publictransport"},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["status"] == "success"
    assert all(r["geometry"] for r in response_data["data"]["routes"])

    route = response_data["data"]["routes"][0]
    assert route["start_time"] == "2020-01-01T01:00:00+01:00"
    assert route["end_time"] == "2020-01-01T01:30:00+01:00"

    geometry = route["geometry"]
    assert geometry["type"] == "FeatureCollection"
    assert geometry["features"][1]["properties"] == {
        "leg_index": 1,
        "direction": "Mairie d'Issy (Issy-les-Moulineaux)",
        "lineColor": "007852",
        "mode": "SUBWAY",
        "num": "12",
        "network": "RATP",
    }

    summary = route["summary"]
    assert list(map(lambda part: part["mode"], summary)) == [
        "WALK",
        "SUBWAY",
        "WALK",
        "SUBWAY",
        "WALK",
    ]

    # Walk summary
    assert summary[0]["info"] is None
    assert summary[0]["distance"] > 0
    assert summary[0]["duration"] > 0

    # Subway summary
    assert summary[1]["info"]["num"] == "12"
    assert summary[1]["info"]["direction"] == "Mairie d'Issy (Issy-les-Moulineaux)"
    assert summary[1]["info"]["lineColor"] == "007852"
    assert summary[1]["info"]["network"] == "RATP"

    # Subway leg
    leg = route["legs"][1]
    assert leg["from"] == {
        "id": "1:4:43789",
        "name": "Lamarck-Caulaincourt",
        "location": [2.339149, 48.889738],
    }
    assert leg["to"] == {"id": "1:4:43790", "name": "Concorde", "location": [2.321412, 48.865489]}
    assert len(leg["stops"]) == 7


def test_directions_public_transport_restricted_areas():
    client = TestClient(app)

    # Paris - South Africa
    response = client.get(
        "http://localhost/v1/directions/2.3211757,48.8604893;22.1741215,-33.1565800",
        params={"language": "fr", "type": "publictransport"},
    )
    assert response.status_code == 422

    # Pekin
    response = client.get(
        "http://localhost/v1/directions/116.2945000,39.9148800;116.4998847,39.9091405",
        params={"language": "fr", "type": "publictransport"},
    )
    assert response.status_code == 422

    #  Washington - New York
    response = client.get(
        "http://localhost/v1/directions/-74.0308525,40.7697215;-77.0427329,38.8581794",
        params={"language": "fr", "type": "publictransport"},
    )
    assert response.status_code == 422


def test_directions_not_configured():
    with override_settings(
        {
            "QWANT_DIRECTIONS_API_BASE_URL": None,
            "MAPBOX_DIRECTIONS_ACCESS_TOKEN": None,
        }
    ):
        client = TestClient(app)
        response = client.get(
            "http://localhost/v1/directions/" "2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
            params={"language": "fr", "type": "driving"},
        )
        assert response.status_code == 501


def test_directions_rate_limiter(limiter_test_normal, mock_directions_car_with_rate_limiter):
    client = TestClient(app)
    # rate limiter is triggered after 30 req/min by default
    for _ in range(40):
        response = client.get(
            "http://localhost/v1/directions/" "2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
            params={"language": "fr", "type": "driving"},
        )
    assert response.status_code == 429
