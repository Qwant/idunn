from contextlib import contextmanager
from copy import deepcopy

from idunn import settings
from idunn.api import places_list
from idunn.api.pages_jaunes import PjSource
from idunn.places import utils as places_utils


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
        try:
            yield
        finally:
            places_utils.pj_source = old_source
            places_list.pj_source = old_source


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
