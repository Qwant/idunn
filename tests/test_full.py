import re
import pytest
import responses
from fastapi.testclient import TestClient
from freezegun import freeze_time
from unittest.mock import ANY

from app import app


@pytest.fixture(scope="function")
def mock_external_requests():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add("GET", re.compile(r"^https://.*\.wikipedia.org/"), status=404)
        yield


@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_full(mock_external_requests):
    """
    Exhaustive test that checks all possible blocks
    """
    client = TestClient(app)
    response = client.get(url=f"http://localhost/v1/pois/osm:way:7777778?lang=es")

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "type": "poi",
        "id": "osm:way:7777778",
        "name": "Fako Allo",
        "local_name": "Fake All",
        "class_name": "museum",
        "subclass_name": "museum",
        "geometry": {
            "coordinates": [2.3250037768187326, 48.86618482685007],
            "type": "Point",
            "center": [2.3250037768187326, 48.86618482685007],
        },
        "address": {
            "admin": None,
            "admins": [
                ANY,
                ANY,
                ANY,
                ANY,
                ANY,
                {
                    "id": "admin:osm:relation:2202162",
                    "class_name": "country",
                    "label": "Francia",
                    "name": "Francia",
                    "postcodes": [],
                },
            ],
            "id": "addr:2.326285;48.859635",
            "label": "62B Rue de Lille (Paris)",
            "name": "62B Rue de Lille",
            "housenumber": "62B",
            "postcode": None,
            "street": {
                "id": "street:553660044C",
                "name": "Rue de Lille",
                "label": "Rue de Lille (Paris)",
                "postcodes": ["75007", "75008"],
            },
            "country_code": "FR",
        },
        "blocks": [
            {
                "type": "opening_hours",
                "status": "open",
                "next_transition_datetime": "2018-06-14T21:45:00+02:00",
                "seconds_before_next_transition": 40500,
                "is_24_7": False,
                "raw": "Tu-Su 09:30-18:00; Th 09:30-21:45",
                "days": [
                    {
                        "dayofweek": 1,
                        "local_date": "2018-06-11",
                        "status": "closed",
                        "opening_hours": [],
                    },
                    {
                        "dayofweek": 2,
                        "local_date": "2018-06-12",
                        "status": "open",
                        "opening_hours": [{"beginning": "09:30", "end": "18:00"}],
                    },
                    {
                        "dayofweek": 3,
                        "local_date": "2018-06-13",
                        "status": "open",
                        "opening_hours": [{"beginning": "09:30", "end": "18:00"}],
                    },
                    {
                        "dayofweek": 4,
                        "local_date": "2018-06-14",
                        "status": "open",
                        "opening_hours": [{"beginning": "09:30", "end": "21:45"}],
                    },
                    {
                        "dayofweek": 5,
                        "local_date": "2018-06-15",
                        "status": "open",
                        "opening_hours": [{"beginning": "09:30", "end": "18:00"}],
                    },
                    {
                        "dayofweek": 6,
                        "local_date": "2018-06-16",
                        "status": "open",
                        "opening_hours": [{"beginning": "09:30", "end": "18:00"}],
                    },
                    {
                        "dayofweek": 7,
                        "local_date": "2018-06-17",
                        "status": "open",
                        "opening_hours": [{"beginning": "09:30", "end": "18:00"}],
                    },
                ],
            },
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
                                "beers": [{"name": "Kilkenny"}, {"name": "Guinness"}],
                            },
                            {
                                "type": "cuisine",
                                "cuisines": [{"name": "Italian"}, {"name": "French"}],
                                "gluten_free": "only",
                                "vegan": "unknown",
                                "vegetarian": "unknown",
                            },
                        ],
                    }
                ],
            },
            {"type": "website", "url": "http://testing.test", "label": None},
            {"type": "contact", "url": "mailto:contact@example.com",},
        ],
        "meta": {"source": "osm"},
    }
