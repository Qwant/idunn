import json
import os

import pytest

from idunn.datasources.tripadvisor import TA_API_BASE_URL


def mock_tripadvisor_api(httpx_mock, filename: str):
    api_result_json = json.load(open(os.path.join(os.path.dirname(__file__), filename)))
    httpx_mock.get(TA_API_BASE_URL).respond(json=api_result_json)
    yield api_result_json


@pytest.fixture
def mock_ta_search_by_hotel_id_api_with_the_hotel_captain_cook(httpx_mock):
    yield from mock_tripadvisor_api(
        httpx_mock, "api_search_by_hotel_id_the_hotel_captain_cook.json"
    )
