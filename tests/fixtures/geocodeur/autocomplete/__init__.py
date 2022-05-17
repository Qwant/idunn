import re
import pytest

from tests.utils import override_settings, read_fixture

BASE_URL = "http://qwant.bragi"
NLU_URL = "http://qwant.nlu/"
CLASSIF_URL = "http://qwant.classif"
ES_URL = "http://qwant.es"

FIXTURE_AUTOCOMPLETE = read_fixture("fixtures/geocodeur/autocomplete/osm/pavillon_paris.json")

FIXTURE_CLASSIF = {
    "pharmacie": read_fixture("fixtures/nlp/classifier/classif_pharmacy.json"),
    "bank": read_fixture("fixtures/nlp/classifier/classif_bank.json"),
}


def mock_NLU_for(httpx_mock, dataset):
    with override_settings({"NLU_TAGGER_URL": NLU_URL, "NLU_CLASSIFIER_URL": CLASSIF_URL}):
        nlu_json = read_fixture(f"fixtures/nlp/nlu/{dataset}.json")
        httpx_mock.post(NLU_URL).respond(json=nlu_json)

        for q, data in FIXTURE_CLASSIF.items():
            httpx_mock.post(
                CLASSIF_URL, json={"text": q, "domain": "poi", "language": "fr", "count": 10}
            ).respond(json=data)

        yield nlu_json


@pytest.fixture
def mock_NLU_with_brand(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_brand")


@pytest.fixture
def mock_NLU_with_brand_and_city(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_brand_and_city")


@pytest.fixture
def mock_NLU_with_cat(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_cat")


@pytest.fixture
def mock_NLU_with_cat_bank(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_cat_bank")


@pytest.fixture
def mock_NLU_with_cat_city_country(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_cat_city_country")


@pytest.fixture
def mock_NLU_with_category_and_city(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_category_and_city")


@pytest.fixture
def mock_NLU_with_poi(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_poi")


@pytest.fixture
def mock_NLU_with_picasso(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_picasso")


@pytest.fixture
def mock_NLU_with_moliere(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_moliere")


@pytest.fixture
def mock_NLU_with_chez_eric(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_chez_eric")


@pytest.fixture()
def mock_NLU_with_city(httpx_mock):
    yield from mock_NLU_for(httpx_mock, "with_city")


@pytest.fixture
def mock_autocomplete_get(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete.*q=bloublou")).respond(
            json=read_fixture("fixtures/geocodeur/autocomplete/osm/empty.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete.*q=(paris|parigi).*")).respond(
            json=read_fixture("fixtures/geocodeur/autocomplete/osm/paris.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete.*q=auchan.*")).respond(
            json=read_fixture("fixtures/geocodeur/autocomplete/osm/auchan.json")
        )

        httpx_mock.get(
            re.compile(rf"^{BASE_URL}/autocomplete.*q=43\+rue\+de\+paris\+rennes.*")
        ).respond(
            json=read_fixture("fixtures/geocodeur/autocomplete/osm/43_rue_de_paris_rennes.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete.*q=hotel.*poi_dataset.*")).respond(
            json=read_fixture("fixtures/geocodeur/autocomplete/tripadvisor/hotel_moliere.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete.*q=chez.*poi_dataset.*")).respond(
            json=read_fixture("fixtures/geocodeur/autocomplete/tripadvisor/chez_eric.json")
        )

        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete")).respond(json=FIXTURE_AUTOCOMPLETE)

        yield


@pytest.fixture
def mock_autocomplete_post(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.post(re.compile(f"^{BASE_URL}/autocomplete")).respond(json=FIXTURE_AUTOCOMPLETE)
        yield


@pytest.fixture
def mock_autocomplete_unavailable(httpx_mock):
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.get(re.compile(f"^{BASE_URL}/autocomplete")).respond(502)
        yield


@pytest.fixture
def mock_bragi_carrefour_in_bbox(request, httpx_mock):
    bragi_response = read_fixture("fixtures/geocodeur/autocomplete/osm/carrefour_in_bbox.json")
    limit = getattr(request, "param", {}).get("limit")
    if limit is not None:
        bragi_response["features"] = bragi_response["features"][:limit]
    with override_settings({"BRAGI_BASE_URL": BASE_URL}):
        httpx_mock.post(re.compile(f"^{BASE_URL}/autocomplete")).respond(json=bragi_response)
        yield
