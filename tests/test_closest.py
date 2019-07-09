from apistar import TestClient

from app import app


def test_v1_metrics_ok():
    client = TestClient(app)
    response = client.get("http://localhost/v1/reverse/48.810273:5.108632")

    assert response.status_code == 200

    assert b'admin:osm:relation:2645341' in response.content
