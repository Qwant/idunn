from starlette.testclient import TestClient

from app import app
from .utils import override_settings


def test_covid19_block():
    with override_settings({"BLOCK_COVID_ENABLED": True, "COVID19_USE_REDIS_DATASET": False}):
        client = TestClient(app)
        response = client.get(url=f"http://localhost/v1/pois/osm:way:7777778?lang=es",)

    assert response.status_code == 200
    resp = response.json()
    covid19_block = next((b for b in resp["blocks"] if b["type"] == "covid19"), None)
    assert covid19_block is not None, "Block of type 'covid19' is missing"
    assert covid19_block["status"] == "open_as_usual"
    assert covid19_block["note"] == "Ceci est une note à propos du confinement"
    assert covid19_block["opening_hours"] is not None
