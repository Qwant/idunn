import os
import json
from contextlib import contextmanager
from copy import deepcopy

import idunn
from idunn import settings
from idunn.api import places_list, instant_answer
from idunn.datasources.recycling import recycling_client
from idunn.datasources.wiki_es import WikiEs
from idunn.utils import place as places_utils


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


def read_fixture(fixture_path):
    return json.load(open(os.path.join(os.path.dirname(__file__), fixture_path), encoding="utf-8"))
