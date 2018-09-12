from apistar import TestClient

from app import app


def test_v1_metrics_ok():
    client = TestClient(app)
    response = client.get("http://localhost/v1/metrics")

    assert response.status_code == 200

    assert b'http_requests_inprogress{handler="apistar_prometheus.handlers.expose_metrics",method="GET"} 1.0' in response.content
