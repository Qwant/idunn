import os
import json
from contextlib import contextmanager
from copy import deepcopy

from idunn import settings
from idunn.api import places_list
from idunn.api.pages_jaunes import PjSource
from idunn.places import utils as places_utils
from idunn.geocoder import nlu_client


@contextmanager
def override_settings(overrides):
    """
    A utility function used by some fixtures to override settings
    """
    old_settings = deepcopy(settings._settings)
    settings._settings.update(overrides)
    try:
        yield
    finally:
        settings._settings = old_settings


@contextmanager
def enable_pj_source():
    old_source = places_list.pj_source
    with override_settings({"PJ_ES": "http://pj_es.test"}):
        new_source = PjSource()
        places_utils.pj_source = new_source
        places_list.pj_source = new_source
        nlu_client.pj_source = new_source
        try:
            yield
        finally:
            places_utils.pj_source = old_source
            places_list.pj_source = old_source
            nlu_client.pj_source = old_source


@contextmanager
def enable_kuzzle():
    """
    We define here settings specific to tests.
    We define kuzzle address and port
    """
    with override_settings({"KUZZLE_CLUSTER_URL": "http://localhost:7512"}):
        yield


@contextmanager
def enable_weather_api():
    """
    We define here settings specific to tests.
    """
    with override_settings(
        {
            "WEATHER_API_URL": "http://api.openweathermap.org/data/2.5/weather?lat=48.5&lon=2.5&mode=json&appid=key&lang=fr",
            "WEATHER_API_KEY": "key",
        }
    ):
        yield


@contextmanager
def enable_recycling():
    """
    We define here settings specific to tests.
    We define the recycling server address and port
    """
    with override_settings({"RECYCLING_SERVER_URL": "http://localhost:7512/trashes/recycling"}):
        yield


@contextmanager
def disable_recycling():
    """
    We define here settings specific to tests.
    We define the recycling server address and port
    """
    with override_settings({"RECYCLING_SERVER_URL": "http://non-existent:1111"}):
        yield


def read_fixture(fixture_path):
    return json.load(open(os.path.join(os.path.dirname(__file__), fixture_path)))
