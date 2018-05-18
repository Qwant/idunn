from apistar.test import TestClient
from app import app


def test_basic_query():
    client = TestClient(app)
    response = client.get(
        url='http://localhost/v1/poi/toto',
        params={'lang': 'fr'}
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "toto",
        "lang": "fr",
        "name": "toto"
    }


def test_schema():
    client = TestClient(app)
    response = client.get(url='http://localhost/schema')

    assert response.status_code == 200  # for the moment we check just that the schema is not empty
