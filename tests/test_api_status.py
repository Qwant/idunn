from starlette.testclient import TestClient
from unittest.mock import patch
from elasticsearch.client import ClusterClient
from elasticsearch.exceptions import ConnectionError

from app import app


def test_v1_status_ok(mimir_es):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "es": {"reachable": True, "running": True},
        "ready": True,
    }


@patch.object(ClusterClient, "health", new=lambda *args: {"status": "red"})
def test_v1_status_es_red(mimir_es):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "es": {"reachable": True, "running": False},
        "ready": False,
    }


@patch.object(ClusterClient, "health")
def test_v1_status_es_unreachable(mock_es_health, mimir_es):
    mock_es_health.side_effect = ConnectionError

    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "es": {"reachable": False, "running": False},
        "ready": False,
    }
