from fastapi.testclient import TestClient
from unittest import mock
import pytest
import json
import os

from app import app
from idunn.datasources.pages_jaunes import LegacyPjSource, ApiPjSource
from idunn.places import utils as places_utils
from .utils import override_settings, init_pj_source


def read_fixture(filename):
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "pj", filename)
    return json.load(open(filepath))


@pytest.fixture
def enable_pj_source(request):
    method, file = request.param
    api_result = read_fixture(f"{file}.json")

    if method == "legacy":
        updated_settings = {"PJ_ES": "http://pj_es.test"}
        source_type = LegacyPjSource
    else:
        updated_settings = {}
        source_type = ApiPjSource

    with override_settings(updated_settings), init_pj_source(source_type):
        if method == "legacy":
            api_mock = mock.patch.object(
                places_utils.pj_source.es,
                "search",
                new=lambda *x, **y: {"hits": {"hits": [api_result]}},
            )
        else:
            api_mock = mock.patch.object(
                places_utils.pj_source, "get_from_params", new=lambda *x, **y: api_result,
            )

        with api_mock:
            yield


@pytest.mark.parametrize(
    "enable_pj_source", [("legacy", "musee_picasso"), ("api", "api_musee_picasso")], indirect=True,
)
def test_pj_place(enable_pj_source):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/pj:05360257?lang=fr")

    assert response.status_code == 200
    resp = response.json()
    assert resp["id"] == "pj:05360257"
    assert resp["name"] == "Musée Picasso"
    assert resp["address"]["label"] == "5 r Thorigny, 75003 Paris"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["type"] == "poi"
    assert resp["meta"]["source"] == "pages_jaunes"
    # TODO
    # assert resp["geometry"]["center"] == [2.362634, 48.859702]

    assert resp["address"]["admins"]
    admin = resp["address"]["admins"][0]
    assert admin["name"] == "Paris"
    assert admin["postcodes"] == ["75003"]

    blocks = resp["blocks"]
    assert blocks[0]["type"] == "opening_hours"
    assert blocks[0]["raw"] == "Tu-Su 10:30-18:00"

    assert blocks[1]["type"] == "phone"
    assert blocks[1]["url"] == "tel:+33185560036"

    assert blocks[2]["blocks"][0]["blocks"][0]["wheelchair"] == "yes"

    assert blocks[3]["type"] == "website"
    assert blocks[3]["url"] == "http://www.museepicassoparis.fr" or blocks[3]["url"].startswith(
        "http://localhost:5000/v1/url?url=http://www.museepicassoparis.fr&hash=b6fc09"
    )

    assert blocks[4]["type"] == "images"
    assert len(blocks[4]["images"]) == 3
    # TODO
    #  assert blocks[4]["images"][0]["source_url"] == "https://[VOIR_TOUTES_PHOTOS]"

    print(blocks)
    assert blocks[5]["type"] == "grades"
    assert blocks[5]["total_grades_count"] == 8
    assert blocks[5]["global_grade"] == 4.0
    assert blocks[5]["url"] == "https://[VOIR_TOUS_AVIS]"


@pytest.mark.parametrize(
    "enable_pj_source",
    [("legacy", "musee_picasso_short"), ("api", "api_musee_picasso_short")],
    indirect=True,
)
def test_pj_place_with_missing_data(enable_pj_source):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/pj:05360257?lang=fr")

    assert response.status_code == 200
    resp = response.json()
    assert resp["id"] == "pj:05360257"
    assert resp["name"] == "Musée Picasso"
    assert resp["address"]["label"] == ""
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["type"] == "poi"
    assert resp["meta"]["source"] == "pages_jaunes"
    # TODO
    #  assert resp["geometry"]["center"] == [2.362634, 48.859702]
