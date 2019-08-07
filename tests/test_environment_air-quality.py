from apistar.test import TestClient
from idunn.blocks.environment import AirQuality
from idunn.places import Admin
import pytest
import json
import os
import responses
import re
from .utils import override_settings

"""
In this module we test the air_quality blocks with kuzzle. Air quality appears when a places (city or suburd)
is called

"""

# places info ok
testee = {
    'id': 'admin:osm:relation:7444',
    'insee': '75056',
    'level': 8,
    'label': 'Paris (75000-75116), Île-de-France, France',
    'name': 'Paris',
    'zip_codes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116'],
    'weight': 0.015276595864042666,
    'coord': {
      'lon': 2.3514992,
      'lat': 48.8566101
    },
    'boundary': {
      'coordinates': [
      ],
      'type': 'MultiPolygon'
    },
    'bbox': [2.224122, 48.8155755, 2.4697602, 48.902156],
    'zone_type': 'city',
    'parent_id': 'admin:osm:relation:71525',
    'codes': [{
      'name': 'ref:FR:MGP',
      'value': 'T1'
    }, {
      'name': 'ref:INSEE',
      'value': '75056'
    }],
    'names': {
      'br': 'Pariz',
      'ca': 'París',
      'de': 'Paris',
      'en': 'Paris',
      'es': 'París',
      'fr': 'Paris',
      'it': 'Parigi'
    },
    'labels': {
      'br': "Pariz (75000-75116), Enez-Frañs, Bro-C'hall",
      'ca': 'París (75000-75116), Illa de França, França',
      'de': 'Paris (75000-75116), Île-de-France, Frankreich',
      'en': 'Paris (75000-75116), Ile-de-France, France',
      'es': 'París (75000-75116), Isla de Francia, Francia',
      'it': 'Parigi (75000-75116), Isola di Francia, Francia'
    }
  }

# places info nok
testee_nok = {
    'id': 'admin:osm:relation:7444',
    'insee': '75056',
    'level': 8,
    'label': 'Paris (75000-75116), Île-de-France, France',
    'name': 'Paris',
    'zip_codes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116'],
    'weight': 0.015276595864042666,
    'coord': {
      'lon': 2.3514992,
      'lat': 48.8566101
    },
    'boundary': {
      'coordinates': [
      ],
      'type': 'MultiPolygon'
    },
    'bbox': [2.224122, 48.8155755, 2.4697602, 48.902156],
    'zone_type': 'region',
    'parent_id': 'admin:osm:relation:71525',
    'codes': [{
      'name': 'ref:FR:MGP',
      'value': 'T1'
    }, {
      'name': 'ref:INSEE',
      'value': '75056'
    }],
    'names': {
      'br': 'Pariz',
      'ca': 'París',
      'de': 'Paris',
      'en': 'Paris',
      'es': 'París',
      'fr': 'Paris',
      'it': 'Parigi'
    },
    'labels': {
      'br': "Pariz (75000-75116), Enez-Frañs, Bro-C'hall",
      'ca': 'París (75000-75116), Illa de França, França',
      'de': 'Paris (75000-75116), Île-de-France, Frankreich',
      'en': 'Paris (75000-75116), Ile-de-France, France',
      'es': 'París (75000-75116), Isla de Francia, Francia',
      'it': 'Parigi (75000-75116), Isola di Francia, Francia'
    }
  }





@pytest.fixture(scope="function")
def kuzzle_test_normal():
    """
    We define here settings specific to tests.
    We define kuzzle address and por
    """
    with override_settings({'KUZZLE_CLUSTER_ADDRESS': 'http://localhost', 'KUZZLE_CLUSTER_PORT': '7512'}):
        yield


def test_pollution_city(kuzzle_test_normal):
    """
    Check result when place is a city
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'kuzzle_air-quality_response.json')

    with open(filepath, "r") as f:
            json_aq = json.load(f)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('POST',
             re.compile(r'^http://localhost:7512/opendatasoft/air_quality/'),
             status=200,
             json=json_aq)


        res = AirQuality.from_es(
            Admin(testee),
            lang='en'
        )
        assert res == AirQuality(
             air_quality={
                 'PM10': {'value': 37.4, 'quality_indice': 5},
                 'O3': {'value': 85.4, 'quality_indice': 2},
                 'SO2': {'value': 509.6, 'quality_indice': 9},
                 'NO2': {'value': 17.3, 'quality_indice': 0},
                 'globlalQuality': 4.0,
                 'date': "2019-08-06T10:00:00.000Z",
                 'source': 'EEA France',
                 'measurements_unit': 'µg/m³'
             }
        )

def test_pollution_from_region(kuzzle_test_normal):
    """
    Check result is none when place is not a city
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'kuzzle_air-quality_response.json')

    with open(filepath, "r") as f:
        json_aq = json.load(f)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('POST',
                 re.compile(r'^http://localhost:7512/eea/air_pollution/'),
                 status=200,
                 json=json_aq)

        res = AirQuality.from_es(
            Admin(testee_nok),
            lang='en'
        )
        assert res == None

def test_pollution_with_no_kuzzle():
    """
    Check the result None when kuzzle url is not set
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'kuzzle_air-quality_response.json')

    with open(filepath, "r") as f:
        json_aq = json.load(f)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('POST',
                 re.compile(r'^http://localhost:7512/eea/air_pollution/'),
                 status=200,
                 json=json_aq)

        res = AirQuality.from_es(
            Admin(testee_nok),
            lang='en'
        )
        assert res == None

