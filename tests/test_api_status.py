from unittest.mock import patch
from apistar import TestClient
from elasticsearch.client import ClusterClient
from elasticsearch.exceptions import ConnectionError

from app import app


def test_v1_status_ok(es):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {"es": {"reachable": True, "running": True}}


@patch.object(ClusterClient, "health", new=lambda *args: {"status": "red"})
def test_v1_status_es_red(es):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {"es": {"reachable":True, "running": False}}


@patch.object(ClusterClient, "health")
def test_v1_status_es_unreachable(mock_es_health, es):
    mock_es_health.side_effect = ConnectionError

    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {"es": {"reachable":False, "running": False}}
