import os
import json
from contextlib import contextmanager
from copy import deepcopy

import idunn
from idunn import settings
from idunn.api import places_list, instant_answer
from idunn.datasources.recycling import recycling_client
from idunn.datasources.wiki_es import WikiEs
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
def init_wiki_es():
    old_es = idunn.blocks.description.wiki_es
    idunn.blocks.description.wiki_es = WikiEs()
    idunn.places.base.wiki_es = WikiEs()

    try:
        yield
    finally:
        idunn.blocks.description.wiki_es = old_es
        idunn.places.base.wiki_es = old_es


@contextmanager
def init_pj_source(source_type):
    old_source = places_list.pj_source
    new_source = source_type()

    instant_answer.pj_source = new_source
    places_utils.pj_source = new_source
    places_list.pj_source = new_source

    try:
        yield
    finally:
        instant_answer.pj_source = old_source
        places_utils.pj_source = old_source
        places_list.pj_source = old_source


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
    with override_settings({"RECYCLING_SERVER_URL": "http://recycling.test"}):
        # No need to authenticate and fetch a token during tests
        recycling_client.session.token_expires_at = 1e60
        yield


@contextmanager
def inaccessible_recycling():
    """
    We define here settings specific to tests.
    We define the recycling server address and port
    """
    with override_settings({"RECYCLING_SERVER_URL": "http://non-existent.test"}):
        yield


def read_fixture(fixture_path):
    return json.load(open(os.path.join(os.path.dirname(__file__), fixture_path)))
