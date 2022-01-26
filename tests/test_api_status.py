import responses
from fastapi.testclient import TestClient
from unittest.mock import patch
from elasticsearch.client.cluster import ClusterClient
from elasticsearch.exceptions import ConnectionError
from app import app
from idunn import settings

from .fixtures.pj import (
    mock_pj_status_with_musee_picasso_short,
)
from .utils import read_fixture

FIXTURE_STATUS = read_fixture("fixtures/bragi_status.json")
FIXTURE_TAGGER_BODY = read_fixture("fixtures/nlp/tagger_body.json")
FIXTURE_CLASSIFIER_BODY = read_fixture("fixtures/nlp/classifier_body.json")


@responses.activate
def test_v1_status_ok(mimir_es, mock_pj_status_with_musee_picasso_short):
    mock_requests()
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "info": {
            "es_mimir": "up",
            "es_wiki": "down",
            "bragi": "up",
            "tagger": "up",
            "classifier": "up",
            "pagesjaunes": "up",
        }
    }


@responses.activate
@patch.object(ClusterClient, "health", new=lambda *args: {"status": "red"})
def test_v1_status_es_red(mimir_es, mock_pj_status_with_musee_picasso_short):
    mock_requests()
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "info": {
            "es_mimir": "down",
            "es_wiki": "down",
            "bragi": "up",
            "tagger": "up",
            "classifier": "up",
            "pagesjaunes": "up",
        }
    }


@responses.activate
@patch.object(ClusterClient, "health")
def test_v1_status_es_unreachable(
    mock_es_health, mimir_es, mock_pj_status_with_musee_picasso_short
):
    mock_requests()
    mock_es_health.side_effect = ConnectionError("N/A", "Mocked connection error", None)

    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "info": {
            "es_mimir": "down",
            "es_wiki": "down",
            "bragi": "up",
            "tagger": "up",
            "classifier": "up",
            "pagesjaunes": "up",
        }
    }


def mock_requests():
    responses.add(
        responses.GET, settings["BRAGI_BASE_URL"] + "/status", json=FIXTURE_STATUS, status=200
    )
    responses.add(responses.POST, settings["NLU_TAGGER_URL"], json=FIXTURE_TAGGER_BODY, status=200)
    responses.add(
        responses.POST, settings["NLU_CLASSIFIER_URL"], json=FIXTURE_CLASSIFIER_BODY, status=200
    )
