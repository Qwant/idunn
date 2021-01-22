import os
import json
import pytest
from app import app
from unittest import mock
from idunn.places import POI
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def orsay_wiki_es(wiki_client, init_indices):
    """
    We load the wiki_es fixture for the orsay museum
    """
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "orsay_wiki_es.json")
    with open(filepath, "r") as f:
        poi = json.load(f)
        poi_id = poi["id"]
        wiki_client.index(
            index="wikidata_fr", body=poi, doc_type="wikipedia", id=poi_id, refresh=True
        )
        return poi_id


def test_orsay_images():
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:way:63178753?lang=fr")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    resp = response.json()

    assert resp["blocks"][4]["type"] == "images"
    assert resp["blocks"][4]["images"] == [
        {
            "url": "https://s2.qwant.com/thumbr/0x0/3/9/43f34b2898978cd1c6cbfa90766ef432d761f02d31f32120eff6db12f616b5/1024px-Logo_musée_d'Orsay.png?u=https%3A%2F%2Fupload.wikimedia.org%2Fwikipedia%2Ffr%2Fthumb%2F7%2F73%2FLogo_mus%25C3%25A9e_d%2527Orsay.png%2F1024px-Logo_mus%25C3%25A9e_d%2527Orsay.png&q=0&b=1&p=0&a=0",
            "alt": "Musée d'Orsay",
            "credits": "",
            "source_url": "https://upload.wikimedia.org/wikipedia/fr/thumb/7/73/Logo_mus%C3%A9e_d%27Orsay.png/1024px-Logo_mus%C3%A9e_d%27Orsay.png",
        },
    ]


@mock.patch.object(POI, "get_name", lambda *x: None)
def test_image_for_unnamed_poi():
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:way:63178753?lang=fr")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    resp = response.json()

    assert resp["blocks"][4]["type"] == "images"
    assert resp["blocks"][4]["images"] == [
        {
            "url": "https://s2.qwant.com/thumbr/0x0/3/9/43f34b2898978cd1c6cbfa90766ef432d761f02d31f32120eff6db12f616b5/1024px-Logo_musée_d'Orsay.png?u=https%3A%2F%2Fupload.wikimedia.org%2Fwikipedia%2Ffr%2Fthumb%2F7%2F73%2FLogo_mus%25C3%25A9e_d%2527Orsay.png%2F1024px-Logo_mus%25C3%25A9e_d%2527Orsay.png&q=0&b=1&p=0&a=0",
            "alt": "",
            "credits": "",
            "source_url": "https://upload.wikimedia.org/wikipedia/fr/thumb/7/73/Logo_mus%C3%A9e_d%27Orsay.png/1024px-Logo_mus%C3%A9e_d%27Orsay.png",
        },
    ]
