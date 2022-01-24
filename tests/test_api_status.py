from fastapi.testclient import TestClient
from unittest.mock import patch
from elasticsearch.client.cluster import ClusterClient
from elasticsearch.exceptions import ConnectionError
from app import app

from .fixtures.pj import (
    mock_pj_status_with_musee_picasso_short,
)


def test_v1_status_ok(mimir_es, mock_pj_status_with_musee_picasso_short):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "info": {
            "es_mimir": "up",
            "es_wiki": "down",
            "nlp": "up",
            "pagesjaunes": "up",
        }
    }


@patch.object(ClusterClient, "health", new=lambda *args: {"status": "red"})
def test_v1_status_es_red(mimir_es, mock_pj_status_with_musee_picasso_short):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "info": {
            "es_mimir": "down",
            "es_wiki": "down",
            "nlp": "up",
            "pagesjaunes": "up",
        }
    }


@patch.object(ClusterClient, "health")
def test_v1_status_es_unreachable(
    mock_es_health, mimir_es, mock_pj_status_with_musee_picasso_short
):
    mock_es_health.side_effect = ConnectionError("N/A", "Mocked connection error", None)

    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "info": {
            "es_mimir": "down",
            "es_wiki": "down",
            "nlp": "up",
            "pagesjaunes": "up",
        }
    }
