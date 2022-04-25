import re
import pytest

from tests.utils import override_settings, read_fixture

BASE_URL = "http://qwant.bragi"
NLU_URL = "http://qwant.nlu/"
CLASSIF_URL = "http://qwant.classif"
ES_URL = "http://qwant.es"

FIXTURE_SEARCH = read_fixture("fixtures/geocodeur/search/osm/pavillon_paris.json")


@pytest.fixture
def mock_search_get(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.get(re.compile(f"^{BASE_URL}/search.*q=bloublou")).respond(
            json=read_fixture("fixtures/geocodeur/search/osm/empty.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/search.*q=(paris|parigi).*")).respond(
            json=read_fixture("fixtures/geocodeur/search/osm/paris.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/search.*q=auchan.*")).respond(
            json=read_fixture("fixtures/geocodeur/search/osm/auchan.json")
        )

        httpx_mock.get(re.compile(rf"^{BASE_URL}/search.*q=43\+rue\+de\+paris\+rennes.*")).respond(
            json=read_fixture("fixtures/geocodeur/search/osm/43_rue_de_paris_rennes.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/search.*q=hotel.*poi_dataset.*")).respond(
            json=read_fixture("fixtures/geocodeur/search/tripadvisor/hotel_moliere.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/search.*q=chez.*poi_dataset.*")).respond(
            json=read_fixture("fixtures/geocodeur/search/tripadvisor/chez_eric.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/search")).respond(json=FIXTURE_SEARCH)

        yield
