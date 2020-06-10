from fastapi.testclient import TestClient

from app import app


def test_v1_metrics_ok():
    client = TestClient(app)
    response = client.get("http://localhost/v1/metrics")

    assert response.status_code == 200

    assert (
        b'http_requests_inprogress{handler="expose_metrics",method="GET"} 1.0' in response.content
    )
