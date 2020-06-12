import re
import pytest
from app import app
from fastapi.testclient import TestClient
from freezegun import freeze_time

from .utils import read_fixture, override_settings

BBOX = "-4.5689169,48.3572972,-4.4278311,48.4595521"
BRAGI_BASE_URL = "http://bragi.test"
BRAGI_RESPONSE = read_fixture("fixtures/autocomplete/carrefour_in_bbox.json")


@pytest.fixture
def mock_autocomplete_post(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BRAGI_BASE_URL}):
        httpx_mock.post(re.compile(f"^{BRAGI_BASE_URL}/autocomplete"), content=BRAGI_RESPONSE)
        yield


@freeze_time("2020-05-14 08:30:00+02:00")
def test_places_bbox_with_osm_query(mock_autocomplete_post):
    client = TestClient(app)

    response = client.get(url=f"http://localhost/v1/places?bbox={BBOX}&q=carrefour&source=osm")

    assert response.status_code == 200

    resp = response.json()
    places = resp["places"]
    assert len(places) == 5

    assert places[0]["name"] == "Carrefour Market"
    assert places[0]["address"]["label"] == "Rue Pierre Trépos (Brest)"
    assert places[0]["address"]["housenumber"] is None
    assert places[0]["address"]["country_code"] == "FR"

    assert places[1]["name"] == "Carrefour"
    assert places[1]["address"]["label"] == "120 Boulevard de Plymouth (Brest)"
    assert places[1]["address"]["housenumber"] == "120"
    assert places[1]["address"]["country_code"] == "FR"
