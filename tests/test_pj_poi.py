from fastapi.testclient import TestClient
import pytest

from app import app

from .fixtures.pj import (
    mock_pj_api_with_musee_picasso,
    mock_pj_api_with_restaurant_petit_pan,
    mock_pj_api_with_hotel_hilton,
    mock_pj_api_with_musee_picasso_short,
)


def test_pj_place(mock_pj_api_with_musee_picasso):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/pj:05360257?lang=fr")

    assert response.status_code == 200
    resp = response.json()
    assert resp["id"] == "pj:05360257"
    assert resp["name"] == "Musée Picasso"
    assert resp["address"]["label"] == "5 rue Thorigny, 75003 Paris"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["type"] == "poi"
    assert resp["meta"] == {
        "source": "pages_jaunes",
        "source_url": "https://www.pagesjaunes.fr/pros/05360257",
        "contribute_url": "https://www.pagesjaunes.fr/pros/05360257#zone-informations-pratiques",
        "maps_directions_url": "https://www.qwant.com/maps/routes/?destination=pj%3A05360257",
        "maps_place_url": "https://www.qwant.com/maps/place/pj:05360257",
    }
    assert resp["geometry"]["center"] == [2.362634, 48.859702]

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
        "http://localhost:5000/v1/redirect?url=http%3A%2F%2Fwww.museepicassoparis.fr&hash=b6fc09"
    )

    assert blocks[4]["type"] == "images"
    assert len(blocks[4]["images"]) == 3

    assert blocks[5]["type"] == "grades"
    assert blocks[5]["total_grades_count"] == 8
    assert blocks[5]["global_grade"] == 4.0
    assert blocks[5]["url"] == "https://www.pagesjaunes.fr/pros/05360257#ancreBlocAvis"


def test_pj_api_place(mock_pj_api_with_musee_picasso):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/pj:05360257?lang=fr")
    assert response.status_code == 200
    resp = response.json()
    blocks = resp["blocks"]

    assert blocks[3]["type"] == "website"
    assert blocks[3]["url"].startswith(
        "http://localhost:5000/v1/redirect?url=http%3A%2F%2Fwww.museepicassoparis.fr&hash=b6fc09"
    )
    assert blocks[3]["label"] == "www.museepicassoparis.fr"

    assert blocks[6]["type"] == "transactional"
    assert blocks[6]["appointment_url"].startswith(
        "http://localhost:5000/v1/redirect?url=https%3A%2F%2F%5BAPPOINTMENT_URL%5D&hash=92710b"
    )

    assert blocks[7]["type"] == "social"
    assert blocks[7]["links"][0]["site"] == "facebook"
    assert blocks[7]["links"][0]["url"].startswith(
        "http://localhost:5000/v1/redirect?url=https%3A%2F%2F%5BFACEBOOK%5D&hash=20eedf5"
    )
    assert blocks[7]["links"][1]["site"] == "twitter"
    assert blocks[7]["links"][1]["url"].startswith(
        "http://localhost:5000/v1/redirect?url=https%3A%2F%2F%5BTWITTER%5D&hash=c34074b"
    )

    assert blocks[8]["type"] == "description"
    assert blocks[8]["source"] == "pagesjaunes"
    assert blocks[8]["description"] == (
        "Le musée Picasso est le musée national français consacré à la vie et à l'œuvre de Pablo "
        "Picasso ainsi qu'aux artistes qui lui furent liés. "
    )

    assert blocks[9]["type"] == "delivery"
    assert blocks[9]["click_and_collect"] == "yes"
    assert blocks[9]["delivery"] == "yes"
    assert blocks[9]["takeaway"] == "unknown"


def test_pj_place_with_missing_data(mock_pj_api_with_musee_picasso_short):
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
    assert resp["geometry"]["center"] == [2.362634, 48.859702]


def test_pj_api_restaurant(mock_pj_api_with_restaurant_petit_pan):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/pj:55452580?lang=fr")
    assert response.status_code == 200
    resp = response.json()
    blocks = resp["blocks"]

    assert blocks[7] == {
        "type": "stars",
        "ratings": [
            {"has_stars": "yes", "nb_stars": None, "kind": "restaurant"},
        ],
    }


def test_pj_api_hotel(mock_pj_api_with_hotel_hilton):
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/pj:55452580?lang=fr")
    assert response.status_code == 200
    resp = response.json()
    blocks = resp["blocks"]

    assert blocks[4] == {
        "type": "stars",
        "ratings": [
            {"has_stars": "yes", "nb_stars": 4.0, "kind": "lodging"},
        ],
    }
