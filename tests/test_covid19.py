from unittest.mock import patch
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app import app
from idunn.blocks import Covid19Block
from idunn.places import POI
from .utils import override_settings


def test_covid19_block():
    with override_settings({"BLOCK_COVID_ENABLED": True, "COVID19_USE_REDIS_DATASET": False}):
        client = TestClient(app)
        response = client.get(url="http://localhost/v1/places/osm:way:7777778?lang=es")

    assert response.status_code == 200
    resp = response.json()
    covid19_block = next((b for b in resp["blocks"] if b["type"] == "covid19"), None)
    assert covid19_block is not None, "Block of type 'covid19' is missing"
    assert covid19_block["status"] == "open_as_usual"
    assert covid19_block["note"] == "Ceci est une note à propos du confinement"
    assert covid19_block["opening_hours"] is not None


def test_covid19_block_unknown_status():
    with override_settings({"BLOCK_COVID_ENABLED": True, "COVID19_USE_REDIS_DATASET": False}):
        client = TestClient(app)
        response = client.get(url="http://localhost/v1/places/osm:node:36153811?lang=fr")

    assert response.status_code == 200
    resp = response.json()
    covid19_block = next((b for b in resp["blocks"] if b["type"] == "covid19"), None)
    assert covid19_block is None, "Block 'covid19' should not be returned"


@freeze_time("2020-04-23 12:00:00+02:00")
@patch.object(POI, "get_country_code", lambda *x: "FR")
def test_covid19_parse_hours():
    with override_settings({"BLOCK_COVID_ENABLED": True, "COVID19_USE_REDIS_DATASET": False}):
        covid_block = Covid19Block.from_es(
            POI(
                {
                    "id": "osm:way:154422021",
                    "coord": {"lon": 2.3, "lat": 48.8},
                    "properties": {
                        "opening_hours": "Tu-Su 08:30-24:00",
                        "opening_hours:covid19": "Tu-Su 08:30-24:00",
                    },
                }
            ),
            lang="en",
        )

    assert covid_block.status == "open_as_usual"
    assert covid_block.note is None
    assert covid_block.opening_hours.raw == "Tu-Su 08:30-24:00"
