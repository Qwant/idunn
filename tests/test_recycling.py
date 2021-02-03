from unittest.mock import ANY
from fastapi.testclient import TestClient
import os
import re
import json
import responses

from .utils import inaccessible_recycling, enable_recycling

from app import app


@enable_recycling()
def test_recycling():
    """
    Check the result of events contained in bbox
    """
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "recycling_response.json")
    with open(filepath, "r") as f:
        recycling_response = json.load(f)

    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            "POST", re.compile(r"^http://recycling.test/.*"), status=200, json=recycling_response,
        )

        response = client.get(url="http://localhost/v1/pois/osm:node:36153800")

        assert response.status_code == 200

        resp = response.json()

    assert resp["id"] == "osm:node:36153800"
    assert resp["name"] == "Poubelle"
    assert len(resp["blocks"]) == 1
    block = resp["blocks"][0]
    assert block["type"] == "recycling"
    assert block == {
        "type": "recycling",
        "containers": [
            {
                "place_description": "camping",
                "type": "recyclable",
                "filling_level": 30,
                "updated_at": "2020-05-26T14:00:00Z",
            },
            {
                "place_description": "camping",
                "type": "glass",
                "filling_level": 60,
                "updated_at": ANY,
            },
            {
                "place_description": "terrain de pétanque ploudal",
                "type": "unknown",
                "filling_level": 90,
                "updated_at": ANY,
            },
        ],
    }


@enable_recycling()
def test_no_recycling_in_bretagne_poi():
    """
    Check that no trash info is provided for a POI in bretagne
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/pois/osm:node:36153811")

    assert response.status_code == 200

    resp = response.json()

    assert resp["id"] == "osm:node:36153811"
    assert resp["name"] == "Multiplexe Liberté"
    assert len([x for x in resp["blocks"] if x["type"] == "recycling"]) == 0


@enable_recycling()
def test_recycling_in_not_bretagne_trash():
    """
    Check that no trash info is provided for a trash which isn't in bretagne
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/pois/osm:node:36153801")
    assert response.status_code == 200

    resp = response.json()
    assert resp["id"] == "osm:node:36153801"
    assert resp["name"] == "Poubelle"
    assert len([x for x in resp["blocks"] if x["type"] == "recycling"]) == 0


@inaccessible_recycling()
def test_recycling_not_enabled():
    """
    Check that no trash info is provided when no trash server is provided.
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/pois/osm:node:36153800")

    assert response.status_code == 200

    resp = response.json()

    assert resp["id"] == "osm:node:36153800"
    assert resp["name"] == "Poubelle"
    assert len([x for x in resp["blocks"] if x["type"] == "recycling"]) == 0
