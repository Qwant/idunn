"""
This module tests basic query against the endpoint '/places/'

The purpose of the 4 following tests 'test_full' is to describe the response
format for each possible spatial objects (Admin, Street, Address, POI).
"""

import urllib
from unittest.mock import ANY
from app import app
from fastapi.testclient import TestClient
from freezegun import freeze_time
from elasticsearch import Elasticsearch, ElasticsearchException
from unittest.mock import patch

from .test_full import OH_BLOCK


def test_full_query_admin():
    """Test the response format to an admin query"""
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/admin:osm:relation:123057?lang=fr")
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp == {
        "type": "admin",
        "id": "admin:osm:relation:123057",
        "name": "Goujounac",
        "local_name": "Goujounac",
        "class_name": "city",
        "subclass_name": "city",
        "geometry": {
            "type": "Point",
            "coordinates": [1.1957467, 44.5756909],
            "center": [1.1957467, 44.5756909],
            "bbox": [1.1777833, 44.5547916, 1.2237663, 44.5978805],
        },
        "address": {
            "admin": {"label": "Goujounac (46250), Lot, Occitanie, France",},
            "admins": [ANY, ANY, ANY],
            "id": None,
            "label": None,
            "name": None,
            "housenumber": None,
            "postcode": "46250",
            "street": {"id": None, "name": None, "label": None, "postcodes": None},
            "country_code": "FR",
        },
        "blocks": [],
        "meta": {
            "source": None,
            "maps_place_url": "https://www.qwant.com/maps/place/admin:osm:relation:123057",
            "maps_directions_url": "https://www.qwant.com/maps/routes/?destination=admin%3Aosm%3Arelation%3A123057",
        },
    }


def test_full_query_street():
    """
        Test the response format to a street query
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/street:35460343?lang=fr")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp == {
        "type": "street",
        "id": "street:35460343",
        "name": "Birnenweg",
        "local_name": "Birnenweg",
        "class_name": "street",
        "subclass_name": "street",
        "geometry": {
            "type": "Point",
            "coordinates": [10.6646915, 53.847809999999996],
            "center": [10.6646915, 53.847809999999996],
        },
        "address": {
            "admin": None,
            "id": None,
            "label": "Birnenweg (Label)",
            "name": "Birnenweg",
            "housenumber": None,
            "postcode": "77777",
            "street": {
                "id": "street:35460343",
                "name": "Birnenweg",
                "label": "Birnenweg (Label)",
                "postcodes": ["77777"],
            },
            "admins": [
                {
                    "id": "admin:osm:relation:27027",
                    "label": "L\u00fcbeck, Schleswig-Holstein, Deutschland",
                    "name": "L\u00fcbeck",
                    "class_name": "state_district",
                    "postcodes": [],
                },
                {
                    "id": "admin:osm:relation:51529",
                    "label": "Schleswig-Holstein, Deutschland",
                    "name": "Schleswig-Holstein",
                    "class_name": "state",
                    "postcodes": [],
                },
                {
                    "id": "admin:osm:relation:51477",
                    "label": "Deutschland",
                    "name": "Deutschland",
                    "class_name": "country",
                    "postcodes": [],
                },
                {
                    "id": "admin:osm:relation:367854",
                    "label": "Sankt Lorenz S\u00fcd, L\u00fcbeck, Schleswig-Holstein, Deutschland",
                    "name": "Sankt Lorenz S\u00fcd",
                    "class_name": "city_district",
                    "postcodes": [],
                },
            ],
            "country_code": "DE",
        },
        "blocks": [],
        "meta": {
            "source": None,
            "maps_place_url": "https://www.qwant.com/maps/place/street:35460343",
            "maps_directions_url": "https://www.qwant.com/maps/routes/?destination=street%3A35460343",
        },
    }


def test_full_query_address():
    """
        Test the response format to an address query
    """
    client = TestClient(app)
    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(url=f"http://localhost/v1/places/{id_moulin}?lang=fr")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp == {
        "type": "address",
        "id": "addr:5.108632;48.810273",
        "name": "4 Rue du Moulin",
        "local_name": "4 Rue du Moulin",
        "class_name": "address",
        "subclass_name": "address",
        "geometry": {
            "type": "Point",
            "coordinates": [5.108632, 48.810273],
            "center": [5.108632, 48.810273],
        },
        "address": {
            "admin": None,
            "id": "addr:5.108632;48.810273",
            "label": "4 Rue du Moulin (Val-d'Ornain)",
            "name": "4 Rue du Moulin",
            "housenumber": "4",
            "postcode": "55000",
            "street": {
                "id": "street:553660045D",
                "name": "Rue du Moulin",
                "label": "Rue du Moulin (Val-d'Ornain)",
                "postcodes": ["55000"],
            },
            "admins": [
                {
                    "id": "admin:osm:relation:7382",
                    "label": "Meuse, Grand Est, France",
                    "name": "Meuse",
                    "class_name": "state_district",
                    "postcodes": [],
                },
                {
                    "id": "admin:osm:relation:3792876",
                    "label": "Grand Est, France",
                    "name": "Grand Est",
                    "class_name": "state",
                    "postcodes": [],
                },
                {
                    "id": "admin:osm:relation:2202162",
                    "label": "France",
                    "name": "France",
                    "class_name": "country",
                    "postcodes": [],
                },
                {
                    "id": "admin:osm:relation:2645341",
                    "label": "Val-d'Ornain (55000), Meuse, Grand Est, France",
                    "name": "Val-d'Ornain",
                    "class_name": "city",
                    "postcodes": ["55000"],
                },
            ],
            "country_code": "FR",
        },
        "blocks": [],
        "meta": {
            "source": None,
            "maps_place_url": "https://www.qwant.com/maps/place/addr:5.108632;48.810273",
            "maps_directions_url": "https://www.qwant.com/maps/routes/?destination=addr%3A5.108632%3B48.810273",
        },
    }


@freeze_time("2018-06-14 8:30:00", tz_offset=0)
def test_full_query_poi():
    """
        Test the response format to a POI query
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:way:63178753?lang=fr")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp["type"] == "poi"
    assert resp["id"] == "osm:way:63178753"
    assert resp["name"] == "Musée d'Orsay"
    assert resp["local_name"] == "Musée d'Orsay"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["geometry"] == {
        "type": "Point",
        "coordinates": [2.3265827716099623, 48.859917803575875],
        "center": [2.3265827716099623, 48.859917803575875],
    }
    assert resp["address"] == {
        "admin": None,
        "id": "addr_poi:osm:way:63178753",
        "label": "1 Rue de la Légion d'Honneur (Paris)",
        "name": "1 Rue de la Légion d'Honneur",
        "housenumber": "1",
        "postcode": "75007",
        "street": {
            "id": "street_poi:osm:way:63178753",
            "name": "Rue de la Légion d'Honneur",
            "label": "Rue de la Légion d'Honneur (Paris)",
            "postcodes": ["75007"],
        },
        "admins": [
            {
                "id": "admin:osm:relation:2188567",
                "label": "Quartier Saint-Thomas-d'Aquin (75007), Paris 7e Arrondissement, Paris, Île-de-France, France",
                "name": "Quartier Saint-Thomas-d'Aquin",
                "class_name": "suburb",
                "postcodes": ["75007"],
            },
            {
                "id": "admin:osm:relation:9521",
                "label": "Paris 7e Arrondissement (75007), Paris, Île-de-France, France",
                "name": "Paris 7e Arrondissement",
                "class_name": "city_district",
                "postcodes": ["75007"],
            },
            {
                "id": "admin:osm:relation:7444",
                "label": "Paris (75000-75116), Île-de-France, France",
                "name": "Paris",
                "class_name": "city",
                "postcodes": [
                    "75000",
                    "75001",
                    "75002",
                    "75003",
                    "75004",
                    "75005",
                    "75006",
                    "75007",
                    "75008",
                    "75009",
                    "75010",
                    "75011",
                    "75012",
                    "75013",
                    "75014",
                    "75015",
                    "75016",
                    "75017",
                    "75018",
                    "75019",
                    "75020",
                    "75116",
                ],
            },
            {
                "id": "admin:osm:relation:71525",
                "label": "Paris, Île-de-France, France",
                "name": "Paris",
                "class_name": "state_district",
                "postcodes": [],
            },
            {
                "id": "admin:osm:relation:8649",
                "label": "Île-de-France, France",
                "name": "Île-de-France",
                "class_name": "state",
                "postcodes": [],
            },
            {
                "id": "admin:osm:relation:2202162",
                "label": "France",
                "name": "France",
                "class_name": "country",
                "postcodes": [],
            },
        ],
        "country_code": "FR",
    }
    assert resp["blocks"] == [
        OH_BLOCK,
        {
            "type": "phone",
            "url": "tel:+33140494814",
            "international_format": "+33 1 40 49 48 14",
            "local_format": "01 40 49 48 14",
        },
        {
            "type": "information",
            "blocks": [
                {
                    "type": "services_and_information",
                    "blocks": [
                        {
                            "type": "accessibility",
                            "wheelchair": "yes",
                            "toilets_wheelchair": "unknown",
                        },
                        {"type": "internet_access", "wifi": True},
                        {
                            "type": "brewery",
                            "beers": [
                                {"name": "Tripel Karmeliet"},
                                {"name": "Delirium"},
                                {"name": "Chouffe"},
                            ],
                        },
                    ],
                }
            ],
        },
        {"type": "website", "url": "http://www.musee-orsay.fr", "label": None},
    ]


def test_type_query_admin():
    client = TestClient(app)
    response = client.get(
        url="http://localhost/v1/places/admin:osm:relation:123057?lang=fr&type=admin",
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp["id"] == "admin:osm:relation:123057"
    assert resp["name"] == "Goujounac"


def test_admin_i18n_name():
    client = TestClient(app)
    response = client.get("http://localhost/v1/places/admin:osm:relation:139610?lang=de")

    assert response.status_code == 200
    resp = response.json()
    assert resp["id"] == "admin:osm:relation:139610"
    assert resp["local_name"] == "Dunkerque"
    assert resp["name"] == "Dünkirchen"
    assert (
        resp["address"]["admin"]["label"]
        == "Dünkirchen (59140-59640), Nord, Nordfrankreich, Frankreich"
    )


def test_type_query_street():
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/street:35460343?lang=fr&type=street")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp["id"] == "street:35460343"
    assert resp["name"] == "Birnenweg"


def test_type_query_address():
    client = TestClient(app)
    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(url=f"http://localhost/v1/places/{id_moulin}?lang=fr&type=address")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp["id"] == "addr:5.108632;48.810273"
    assert resp["name"] == "4 Rue du Moulin"


def test_type_query_poi():
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:way:63178753?lang=fr&type=poi")

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp["id"] == "osm:way:63178753"
    assert resp["name"] == "Musée d'Orsay"
    assert resp["local_name"] == "Musée d'Orsay"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["blocks"][0]["type"] == "opening_hours"
    assert resp["blocks"][1]["type"] == "phone"
    assert not resp["blocks"][0]["is_24_7"]


def test_type_unknown():
    client = TestClient(app)

    id_moulin = urllib.parse.quote_plus("addr:5.108632;48.810273")

    response = client.get(url=f"http://localhost/v1/places/{id_moulin}?lang=fr&type=globibulga")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.enum"


def test_not_found_with_type():
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/street:4242?lang=fr&type=poi")
    assert response.status_code == 404
    assert response.json() == {"detail": "place 'street:4242' not found with type=poi"}


def test_invalid_place_id():
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/invalid_place?lang=fr")
    assert response.status_code == 404


def test_redirect_obsolete_address_with_lat_lon():
    client = TestClient(app)
    response = client.get(
        url="http://localhost/v1/places/addr:-1.12;45.6?lang=fr", allow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/v1/places/latlon:45.60000:-1.12000?lang=fr"


def test_redirect_obsolete_address_with_url_prefix():
    client = TestClient(app)
    response = client.get(
        url="http://localhost/v1/places/addr:-1.12;45.6?lang=fr",
        headers={"x-forwarded-prefix": "/maps/detail/"},
        allow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/maps/detail/v1/places/latlon:45.60000:-1.12000?lang=fr"


def test_basic_short_query_poi():
    client = TestClient(app)
    response = client.get(
        url="http://localhost/v1/places/osm:way:63178753?lang=fr&verbosity=short",
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"

    resp = response.json()

    assert resp["id"] == "osm:way:63178753"
    assert resp["name"] == "Musée d'Orsay"
    assert resp["local_name"] == "Musée d'Orsay"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["blocks"][0]["type"] == "opening_hours"
    assert len(resp["blocks"]) == 1  # it contains only the block opening hours


def test_wrong_verbosity():
    client = TestClient(app)

    response = client.get(
        url="http://localhost/v1/places/osm:way:63178753?lang=fr&verbosity=shoooooort",
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.enum"


def mock_search(detail, *args, **kwargs):
    raise ElasticsearchException


@patch.object(Elasticsearch, "search", new=mock_search)
def test_no_es():
    client = TestClient(app)

    response = client.get(url="http://localhost/v1/places/osm:way:63178753?lang=fr&type=poi")
    assert response.status_code == 503
