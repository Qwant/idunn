from unittest.mock import ANY
from app import app
from fastapi.testclient import TestClient
from freezegun import freeze_time

from .fixtures.api.pj import mock_pj_api_with_musee_picasso_short
from .test_full import OH_BLOCK

BBOX_PARIS = "2.252876,48.819862,2.395707,48.891132"
BBOX_BREST = "-4.807542,48.090743,-4.097541,48.800743"
INVALID_BBOX_PARIS_LEFT_PERM_RIGHT = "2.395707,48.819862,2.252876,48.891132"
INVALID_BBOX_PARIS_MISSING = "48.819862,2.252876,48.891132"


@freeze_time("2021-11-29 8:30:00", tz_offset=2)
def test_bbox_should_trigger_tripadvisor_sources_anywhere_on_hotel_category():
    client = TestClient(app)

    response = client.get(url=f"http://localhost/v1/places?bbox={BBOX_PARIS}&category=hotel")

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "bbox": [2.326583, 48.859918, 2.336234, 48.86538],
        "source": "tripadvisor",
        "bbox_extended": False,
        "places": [
            {
                "address": ANY,
                "blocks": [],
                "class_name": "hotel",
                "geometry": ANY,
                "id": "ta:way:63178753",
                "local_name": "Bergrestaurant Suecka",
                "meta": ANY,
                "name": "Bergrestaurant Suecka",
                "subclass_name": "hotel",
                "type": "poi",
            },
            {
                "address": ANY,
                "blocks": [],
                "class_name": "lodging",
                "geometry": ANY,
                "id": "ta:node:5286293722",
                "local_name": "Hôtel Molière",
                "meta": ANY,
                "name": "Hôtel Molière",
                "subclass_name": "lodging",
                "type": "poi",
            },
        ],
    }


@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_size_list():
    """
    Test the bbox query with a list size=1:
    Same test as test_bbox but with a max list size of 1
    """
    client = TestClient(app)

    response = client.get(
        url=f"http://localhost/v1/places?bbox={BBOX_PARIS}&category=bakery&size=1"
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "source": "osm",
        "bbox": ANY,
        "bbox_extended": False,
        "places": [
            {
                "type": "poi",
                "id": "osm:way:63178753",
                "name": "Musee d'Orsay",
                "local_name": "Musée d'Orsay",
                "class_name": "museum",
                "subclass_name": "museum",
                "geometry": {
                    "type": "Point",
                    "coordinates": [2.3265827716099623, 48.859917803575875],
                    "center": [2.3265827716099623, 48.859917803575875],
                },
                "address": ANY,
                "blocks": [
                    OH_BLOCK,
                    {
                        "international_format": "+33 1 40 49 48 14",
                        "local_format": "01 40 49 48 14",
                        "type": "phone",
                        "url": "tel:+33140494814",
                    },
                    {
                        "type": "website",
                        "url": "http://www.musee-orsay.fr",
                        "label": "www.musee-orsay.fr",
                    },
                    {
                        "type": "social",
                        "links": [
                            {
                                "site": "facebook",
                                "url": "https://www.facebook.com/MuseeOrsay",
                            },
                            {
                                "site": "twitter",
                                "url": "https://twitter.com/MuseeOrsay",
                            },
                            {
                                "site": "instagram",
                                "url": "https://www.instagram.com/MuseeOrsay",
                            },
                            {
                                "site": "youtube",
                                "url": "https://www.youtube.com/MuseeOrsayOfficiel",
                            },
                        ],
                    },
                ],
                "meta": ANY,
            }
        ],
    }


def test_extend_bbox():
    client = TestClient(app)
    small_bbox = "2.350,48.850,2.351,48.851"

    response = client.get(url=f"http://localhost/v1/places?bbox={small_bbox}&category=museum")
    assert response.status_code == 200
    assert len(response.json()["places"]) == 0

    response = client.get(
        url=f"http://localhost/v1/places?bbox={small_bbox}&category=museum&extend_bbox=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["places"]) == 1
    assert data["bbox_extended"] is True
    assert data["bbox"] == [2.338028, 48.861147, 2.338028, 48.861147]


def test_invalid_bbox():
    """
    Test an invalid bbox query:
    """
    client = TestClient(app)

    response = client.get(
        url=f"http://localhost/v1/places?bbox={INVALID_BBOX_PARIS_LEFT_PERM_RIGHT}&category=place_of_worship"
    )

    assert response.status_code == 400

    resp = response.json()

    assert resp == {
        "detail": [{"loc": ["bbox"], "msg": "bbox dimensions are invalid", "type": "value_error"}]
    }

    response = client.get(
        url=f"http://localhost/v1/places?bbox={INVALID_BBOX_PARIS_MISSING}&category=place_of_worship"
    )

    assert response.status_code == 400

    resp = response.json()

    assert resp == {
        "detail": [{"loc": ["bbox"], "msg": "bbox should contain 4 numbers", "type": "value_error"}]
    }


def test_category_or_q():
    """
    Test we get a 400 if none of category or q is present:
    """
    client = TestClient(app)

    response = client.get(url=f"http://localhost/v1/places?bbox={BBOX_PARIS}")

    assert response.status_code == 400
    resp = response.json()
    assert resp == {"detail": "One of 'category' or 'q' parameter is required"}


def test_valid_category_that_trigger_tripadvisor_over_osm():
    """
    Test a valid category filter which should fetch only one cinema in a bbox around Brest city with tripadvisor
    """
    client = TestClient(app)

    response = client.get(url=f"http://localhost/v1/places?bbox={BBOX_BREST}&category=leisure")

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "source": "tripadvisor",
        "places": [
            {
                "type": "poi",
                "id": "ta:node:36153811",
                "name": "Multiplexe Liberté",
                "local_name": "Multiplexe Liberté",
                "class_name": "cinema",
                "subclass_name": "cinema",
                "geometry": ANY,
                "address": ANY,
                "blocks": [],
                "meta": {
                    "source": "tripadvisor",
                    "source_url": ANY,
                    "contribute_url": ANY,
                    "maps_place_url": ANY,
                    "maps_directions_url": ANY,
                    "rating_url": None,
                    "rating_url_noicon": None,
                },
            }
        ],
        "bbox": ANY,
        "bbox_extended": False,
    }


def test_places_with_explicit_source_osm(mock_pj_api_with_musee_picasso_short):
    """
    If source=osm is passed to the query, pj_source should be ignored
    """
    client = TestClient(app)
    response = client.get(
        url=f"http://localhost/v1/places?bbox={BBOX_BREST}&category=leisure&source=osm"
    )

    assert response.status_code == 200
    resp = response.json()

    assert resp == {
        "source": "osm",
        "places": [
            {
                "type": "poi",
                "id": "osm:node:36153811",
                "name": "Multiplexe Liberté",
                "local_name": "Multiplexe Liberté",
                "class_name": "cinema",
                "subclass_name": "cinema",
                "geometry": ANY,
                "address": ANY,
                "blocks": [],
                "meta": {
                    "source": "osm",
                    "source_url": ANY,
                    "contribute_url": ANY,
                    "maps_place_url": ANY,
                    "maps_directions_url": ANY,
                    "rating_url": None,
                    "rating_url_noicon": None,
                },
            }
        ],
        "bbox": ANY,
        "bbox_extended": False,
    }


def test_invalid_category():
    """
    Test we get a 400 if the parameter category is invalid:
    """
    client = TestClient(app)
    response = client.get(
        url=f"http://localhost/v1/places?bbox={BBOX_PARIS}&category=supppermarket"
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.enum"


def test_endpoint_categories():
    """
    Test the endpoint 'categories':
    """
    client = TestClient(app)

    response = client.get(url="http://localhost/v1/categories")

    assert response.status_code == 200

    resp = response.json()
    assert len(resp["categories"]) > 1


def test_category_with_cuisine_filter():
    client = TestClient(app)
    response = client.get(
        url=f"http://localhost/v1/places?bbox={BBOX_BREST}&category=food_crepe&source=osm"
    )

    assert response.status_code == 200
    resp = response.json()
    assert len(resp["places"]) == 1
    assert resp["places"][0]["name"] == "La Crêpe Flambée"
