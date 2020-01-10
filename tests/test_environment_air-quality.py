from idunn.blocks.environment import AirQuality
from idunn.places import Admin
import json
import os
import responses
import re

from .utils import enable_kuzzle

"""
In this module we test the air_quality blocks with kuzzle. Air quality appears when an admin (city or suburd)
is called

"""

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
    "codes": [{"name": "ref:FR:MGP", "value": "T1"}, {"name": "ref:INSEE", "value": "75056"},],
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
    "codes": [{"name": "ref:FR:MGP", "value": "T1"}, {"name": "ref:INSEE", "value": "75056"},],
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


@enable_kuzzle()
def test_pollution_city():
    """
    Check result when place is a city
    """
    filepath = os.path.join(
        os.path.dirname(__file__), "fixtures", "kuzzle_air-quality_response.json"
    )

    with open(filepath, "r") as f:
        json_aq = json.load(f)

    with responses.RequestsMock() as rsps:
        rsps.add(
            "POST",
            re.compile(r"^http://localhost:7512/opendatasoft/air_quality/"),
            status=200,
            json=json_aq,
        )

        res = AirQuality.from_es(Admin(testee), lang="en")

    res2 = AirQuality(
        **{
            "CO": None,
            "PM10": {"value": 37.4, "quality_index": 3},
            "O3": {"value": 85.4, "quality_index": 2},
            "SO2": {"value": 509.6, "quality_index": 5},
            "NO2": {"value": 17.3, "quality_index": 1},
            "PM2_5": {"value": 5.3, "quality_index": 1},
            "date": "2019-08-06T10:00:00.000Z",
            "source": "EEA France",
            "source_url": "http://airindex.eea.europa.eu/",
            "measurements_unit": "µg/m³",
            "quality_index": 5,
        }
    )
    assert res == res2


@enable_kuzzle()
def test_pollution_from_region():
    """
    Check result is none when place is not a city
    """
    res = AirQuality.from_es(Admin(testee_nok), lang="en")
    assert res == None


def test_pollution_with_no_kuzzle():
    """
    Check the result None when kuzzle url is not set
    """
    res = AirQuality.from_es(Admin(testee_nok), lang="en")
    assert res == None
