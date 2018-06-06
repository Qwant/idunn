from unittest.mock import patch
from apistar import TestClient
from elasticsearch.client import ClusterClient

from app import app


def test_v1_status(es):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {"es": {"running": True}}


@patch.object(ClusterClient, "health", new=lambda *args: {"status": "red"})
def test_v1_status_es_red(es):
    client = TestClient(app)
    response = client.get("http://localhost/v1/status")

    assert response.status_code == 200
    assert response.json() == {"es": {"running": False}}
