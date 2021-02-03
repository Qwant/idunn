"""
In this module we test the air_quality blocks with kuzzle. Air quality appears when an admin (city
or suburd) is called.
"""

from idunn.blocks.environment import AirQuality
from idunn.places import Admin
import json
import os
import responses
import re

from .utils import enable_kuzzle
from .test_environment_weather import testee, testee_nok


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
    assert res is None


def test_pollution_with_no_kuzzle():
    """
    Check the result None when kuzzle url is not set
    """
    res = AirQuality.from_es(Admin(testee_nok), lang="en")
    assert res is None
