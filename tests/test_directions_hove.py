import json
import os
import pytest
import re
import urllib.parse
from app import app
from fastapi.testclient import TestClient

from idunn.utils.settings import settings
from .utils import override_settings


FIXTURE_PATH_PT = "directions/hove_public_transports.json"
HOVE_API_URL = settings["HOVE_API_BASE_URL"]


@pytest.fixture
def mock_directions_pt(httpx_mock):
    with override_settings({"HOVE_API_TOKEN": "test"}):
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", FIXTURE_PATH_PT)
        fixture = json.load(open(fixture_path))
        yield httpx_mock.get(re.compile(rf"^{HOVE_API_URL}")).respond(json=fixture)


def test_directions_pt(mock_directions_pt):
    client = TestClient(app)

    response = client.get(
        "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={"type": "publictransport"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert len(response_data["data"]["routes"]) == 4

    route = response_data["data"]["routes"][0]
    steps = route["legs"][0]["steps"]

    assert (
        [s["mode"] for s in route["summary"]]
        == [leg["mode"] for leg in route["legs"]]
        == ["WALK", "SUBWAY", "WALK", "SUBWAY", "WALK"]
    )

    assert [step["maneuver"]["modifier"] for step in steps] == [
        "straight",
        "straight",
        "right",
        "left",
    ]

    assert route["summary"][0] == {
        "distance": 169,
        "duration": 151,
        "info": None,
        "mode": "WALK",
    }

    assert steps[0]["maneuver"] == {
        "location": [2.3402355, 48.8900732],
        "modifier": "straight",
        "detail": {
            "direction": 0,
            "duration": 83,
            "length": 93,
            "name": "Rue Darwin",
        },
        "type": "",
        "instruction": "",
    }

    # Check mocked request seems in accordance with the mocked one
    mocked_url = urllib.parse.unquote(str(mock_directions_pt.calls[0].request.url))
    assert "from=2.34024;48.89007" in mocked_url
    assert "to=2.36886;48.85299" in mocked_url
    assert "direct_path=none" in mocked_url
    assert "datetime" not in mocked_url


def test_directions_hove_not_configured():
    with override_settings({"HOVE_API_TOKEN": None}):
        client = TestClient(app)
        response = client.get(
            "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
            params={"type": "publictransport"},
        )
        assert response.status_code == 501


def test_direction_hove_arrive_by(mock_directions_pt):
    client = TestClient(app)
    client.get(
        "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={
            "type": "publictransport",
            "arrive_by": "2018-06-14T10:30:00",
        },
    )

    mocked_request_url = str(mock_directions_pt.calls[0].request.url)
    assert "datetime" in mocked_request_url
    assert "datetime_represents=arrival" in mocked_request_url


def test_direction_hove_depart_at(mock_directions_pt):
    client = TestClient(app)
    client.get(
        "http://localhost/v1/directions/2.3402355%2C48.8900732%3B2.3688579%2C48.8529869",
        params={
            "type": "publictransport",
            "depart_at": "2018-06-14T10:30:00",
        },
    )

    mocked_request_url = str(mock_directions_pt.calls[0].request.url)
    assert "datetime" in mocked_request_url
    assert "datetime_represents=departure" in mocked_request_url
