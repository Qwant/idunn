import os
import json
import pytest
from unittest.mock import ANY
from fastapi.testclient import TestClient
from app import app

from idunn.blocks.images import ImagesBlock
from idunn.places import OsmPOI, PjApiPOI
from idunn.places.models.pj_find import Listing


@pytest.fixture(scope="module")
def orsay_wiki_es(wiki_client, init_indices):
    """
    We load the wiki_es fixture for the orsay museum
    """
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "wiki", "orsay_wiki_es.json")
    with open(filepath, "r", encoding="utf-8") as f:
        poi = json.load(f)
        poi_id = poi["id"]
        wiki_client.index(
            index="wikidata_fr", body=poi, doc_type="wikipedia", id=poi_id, refresh=True
        )
        yield poi_id
        wiki_client.delete(index="wikidata_fr", doc_type="wikipedia", id=poi_id, refresh=True)


def test_wiki_image(orsay_wiki_es):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:way:63178753?lang=fr")

    assert response.status_code == 200
    resp = response.json()

    assert resp["blocks"][4]["type"] == "images"
    assert resp["blocks"][4]["images"] == [
        {
            "url": "https://s1.qwant.com/thumbr/0x165/e/a/cfd65707824a034b9b1d0429ec68590f13cf2d79ebda2ae65e5028a4f70cdd/1024px-Logo_musée_d'Orsay.png?u=https%3A%2F%2Fupload.wikimedia.org%2Fwikipedia%2Ffr%2Fthumb%2F7%2F73%2FLogo_mus%25C3%25A9e_d%2527Orsay.png%2F1024px-Logo_mus%25C3%25A9e_d%2527Orsay.png&q=0&b=1&p=0&a=0",
            "alt": "Musée d'Orsay",
            "credits": "",
            "source_url": "https://upload.wikimedia.org/wikipedia/fr/thumb/7/73/Logo_mus%C3%A9e_d%27Orsay.png/1024px-Logo_mus%C3%A9e_d%27Orsay.png",
        },
    ]


def test_tag_image():
    block = ImagesBlock.from_es(
        OsmPOI(
            {
                "id": "osm:way:154422021",
                "properties": {
                    "name": "Musée du Louvre",
                    "image": "http://upload.wikimedia.org/wikipedia/commons/6/66/Louvre_Museum_Wikimedia_Commons.jpg",
                },
            }
        ),
        lang="en",
    )
    assert block.dict() == {
        "type": "images",
        "images": [
            {
                "url": ANY,
                "alt": "Musée du Louvre",
                "credits": "",
                "source_url": "https://commons.wikimedia.org/wiki/File:Louvre_Museum_Wikimedia_Commons.jpg#/media/File:Louvre_Museum_Wikimedia_Commons.jpg",
            }
        ],
    }


def test_tag_image_unamed_poi():
    block = ImagesBlock.from_es(
        OsmPOI(
            {
                "id": "osm:way:154422021",
                "properties": {
                    "image": "http://upload.wikimedia.org/wikipedia/commons/6/66/Louvre_Museum_Wikimedia_Commons.jpg"
                },
            }
        ),
        lang="en",
    )
    assert block.dict() == {
        "type": "images",
        "images": [
            {
                "url": ANY,
                "alt": "",
                "credits": "",
                "source_url": "https://commons.wikimedia.org/wiki/File:Louvre_Museum_Wikimedia_Commons.jpg#/media/File:Louvre_Museum_Wikimedia_Commons.jpg",
            }
        ],
    }


def test_pj_poi_no_image():
    block = ImagesBlock.from_es(PjApiPOI(Listing()), lang="fr")
    assert block is None


def test_image_tag_wikipedia():
    block = ImagesBlock.from_es(
        OsmPOI(
            {
                "id": "osm:way:154422021",
                "properties": {
                    "image": "https://fr.wikipedia.org/wiki/Fichier:Tour_Eiffel_Wikimedia_Commons.jpg"
                },
            }
        ),
        lang="fr",
    )
    assert block is None
