import os
import json
import re
import pytest
from app import app
from fastapi.testclient import TestClient
from freezegun import freeze_time
from idunn import settings
from idunn.utils import rate_limiter
from idunn.utils.redis import get_redis_pool

from .test_rate_limiter import disable_redis, limiter_test_normal
from .utils import override_settings


@pytest.fixture
def mock_directions_car(httpx_mock):
    with override_settings({"MAPBOX_DIRECTIONS_ACCESS_TOKEN": "test"}):
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures/directions/qwant_directions_car.json"
        )

        fixture = json.load(open(fixture_path))
        yield httpx_mock.get(re.compile(r"^https://api.mapbox.com/")).respond(json=fixture)


@pytest.fixture
def mock_directions_car_with_rate_limiter(redis, mock_directions_car):
    with override_settings({"REDIS_URL": redis}):
        rate_limiter.redis_pool = get_redis_pool(settings["RATE_LIMITER_REDIS_DB"])
        yield

    # reset rate_limiter to default redis connection url
    rate_limiter.redis_pool = None


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
    assert "exclude=ferry" in str(mock_directions_car.calls[0].request.url)


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
    mocked_request_url = str(mock_directions_car.calls[0].request.url)
    assert "exclude=ferry" in mocked_request_url
    assert "2.34023,48.89007;2.32658,48.85992" in mocked_request_url


def test_mapbox_directions_not_configured():
    with override_settings(
        {
            "MAPBOX_DIRECTIONS_ACCESS_TOKEN": None,
        }
    ):
        client = TestClient(app)
        response = client.get(
            "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
            params={"language": "fr", "type": "driving"},
        )
        assert response.status_code == 501


def test_directions_rate_limiter(limiter_test_normal, mock_directions_car_with_rate_limiter):
    client = TestClient(app)
    # rate limiter is triggered after 30 req/min by default
    for _ in range(40):
        response = client.get(
            "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
            params={"language": "fr", "type": "driving"},
            headers={"x-client-hash": "test-client-hash-value"},
        )
    assert response.status_code == 429
