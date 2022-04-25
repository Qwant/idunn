"""
In this module we test the air_quality blocks with kuzzle. Air quality appears when an admin (city
or suburd) is called.
"""

from pydantic import ValidationError
from pytest import raises

from idunn.blocks.environment import Weather
from idunn.places import Admin
import json
import os
import responses
import re
from .utils import enable_weather_api


# places info ok (correspond to city or suburd)
testee = {
    "id": "admin:osm:relation:7444",
    "insee": "75056",
    "level": 8,
    "label": "Paris (75000-75116), Île-de-France, France",
    "name": "Paris",
    "zip_codes": [
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
    "weight": 0.015276595864042666,
    "coord": {"lon": 2.3514992, "lat": 48.8566101},
    "boundary": {"coordinates": [], "type": "MultiPolygon"},
    "bbox": [2.224122, 48.8155755, 2.4697602, 48.902156],
    "zone_type": "city",
    "parent_id": "admin:osm:relation:71525",
    "codes": [{"name": "ref:FR:MGP", "value": "T1"}, {"name": "ref:INSEE", "value": "75056"}],
    "names": {
        "br": "Pariz",
        "ca": "París",
        "de": "Paris",
        "en": "Paris",
        "es": "París",
        "fr": "Paris",
        "it": "Parigi",
    },
    "labels": {
        "br": "Pariz (75000-75116), Enez-Frañs, Bro-C'hall",
        "ca": "París (75000-75116), Illa de França, França",
        "de": "Paris (75000-75116), Île-de-France, Frankreich",
        "en": "Paris (75000-75116), Ile-de-France, France",
        "es": "París (75000-75116), Isla de Francia, Francia",
        "it": "Parigi (75000-75116), Isola di Francia, Francia",
    },
}

# places info nok (correspond to region)
testee_nok = {
    "id": "admin:osm:relation:7444",
    "insee": "75056",
    "level": 8,
    "label": "Paris (75000-75116), Île-de-France, France",
    "name": "Paris",
    "zip_codes": [
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
    "weight": 0.015276595864042666,
    "coord": {"lon": 2.3514992, "lat": 48.8566101},
    "boundary": {"coordinates": [], "type": "MultiPolygon"},
    "bbox": [2.224122, 48.8155755, 2.4697602, 48.902156],
    "zone_type": "state",
    "parent_id": "admin:osm:relation:71525",
    "codes": [{"name": "ref:FR:MGP", "value": "T1"}, {"name": "ref:INSEE", "value": "75056"}],
    "names": {
        "br": "Pariz",
        "ca": "París",
        "de": "Paris",
        "en": "Paris",
        "es": "París",
        "fr": "Paris",
        "it": "Parigi",
    },
    "labels": {
        "br": "Pariz (75000-75116), Enez-Frañs, Bro-C'hall",
        "ca": "París (75000-75116), Illa de França, França",
        "de": "Paris (75000-75116), Île-de-France, Frankreich",
        "en": "Paris (75000-75116), Ile-de-France, France",
        "es": "París (75000-75116), Isla de Francia, Francia",
        "it": "Parigi (75000-75116), Isola di Francia, Francia",
    },
}


@enable_weather_api()
def test_weather_city():
    """
    Check result when place is a city
    """
    filepath = os.path.join(
        os.path.dirname(__file__), "fixtures", "api", "api_weather_response.json"
    )

    with open(filepath, "r") as f:
        json_aq = json.load(f)

    with responses.RequestsMock() as rsps:
        rsps.add(
            "GET", re.compile(r"^http://api.openweathermap.org/data/2.5/"), status=200, json=json_aq
        )

        res = Weather.from_es(Admin(testee), lang="en")

    assert res == Weather(
        **{
            "temperature": 291.89,
            "icon": "01d",
        }
    )


@enable_weather_api()
def test_wrong_icon_value():
    """
    Raise exception when icon is wrong value
    """
    with raises(ValidationError):
        Weather(
            **{
                "temperature": 291.89,
                "icon": "01g",
            }
        )


@enable_weather_api()
def test_weather_from_region():
    """
    Check result is none when place is not a city
    """
    res = Weather.from_es(Admin(testee_nok), lang="en")
    assert res is None


def test_weather_with_no_kuzzle():
    """
    Check the result None when kuzzle url is not set
    """
    res = Weather.from_es(Admin(testee_nok), lang="en")
    assert res is None
