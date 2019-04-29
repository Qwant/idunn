from contextlib import contextmanager
from copy import deepcopy

from idunn import settings
from idunn.api import places, places_list
from idunn.api.pages_jaunes import PjSource


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
    old_source = places.pj_source
    with override_settings({'PJ_ES': 'http://pj_es.test'}):
        new_source = PjSource()
        places.pj_source = new_source
        places_list.pj_source = new_source
        try:
            yield
        finally:
            places.pj_source = old_source
            places_list.pj_source = old_source
