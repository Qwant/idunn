from starlette.testclient import TestClient
import os
import re
import json
import responses
from .utils import enable_recycling

from app import app


@enable_recycling()
def test_recycling():
    """
    Check the result of events contained in bbox
    """
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "recycling_response.json")
    with open(filepath, "r") as f:
        json_event = json.load(f)

    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            "GET",
            re.compile(r"^http://localhost:7512/trashes/recycling/osm:node:36153800"),
            status=200,
            json=json_event,
        )

        response = client.get(
            url=f"http://localhost/v1/pois/osm:node:36153800",
        )

        assert response.status_code == 200

        resp = response.json()

    assert resp["id"] == "osm:node:36153800"
    # TODO: why is there no name?!
    # assert resp["name"] == "Poubelle"
    assert len(resp["blocks"]) == 1
    block = resp["blocks"][0]
    assert block["type"] == "recycling"
    assert block["volume"] == 70
    assert block["last_update"] == "01-01-1970"
