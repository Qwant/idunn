import json
import os
from unittest import mock

import pytest

from idunn.datasources.pages_jaunes import PagesJaunes
from idunn.utils import place as places_utils
from tests.utils import init_pj_source, override_settings


def mock_pj_api(type_api: str, filename: str):
    api_result = json.load(open(os.path.join(os.path.dirname(__file__), filename)))
    updated_settings = {}
    source_type = PagesJaunes

    with override_settings(updated_settings), init_pj_source(source_type):
        if type_api == "api":
            api_mock = mock.patch.object(
                places_utils.pj_source,
                "get_from_params",
                new=lambda *x, **y: api_result,
            )
            with api_mock:
                yield
        else:
            api_mock = mock.patch.object(
                places_utils.pj_source,
                "get_from_params",
                new=lambda *x, **y: {"search_results": {"listings": [api_result]}},
            )
            with api_mock:
                yield


@pytest.fixture
def mock_pj_api_with_musee_picasso():
    yield from mock_pj_api("api", "api_musee_picasso.json")


@pytest.fixture
def mock_pj_api_with_musee_picasso_short():
    yield from mock_pj_api("api", "api_musee_picasso_short.json")


@pytest.fixture
def mock_pj_api_with_restaurant_petit_pan():
    yield from mock_pj_api("api", "api_restaurant_petit_pan.json")


@pytest.fixture
def mock_pj_api_with_hotel_hilton():
    yield from mock_pj_api("api", "api_hotel_hilton.json")


@pytest.fixture
def mock_pj_api_find_with_musee_picasso():
    yield from mock_pj_api("api_find", "api_musee_picasso.json")


@pytest.fixture
def mock_pj_api_find_with_chez_eric():
    yield from mock_pj_api("api_find", "api_chez_eric.json")
