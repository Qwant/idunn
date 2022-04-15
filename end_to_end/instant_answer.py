import os

from fastapi.testclient import TestClient

os.environ['IS_TEST'] = 'true'

from app import app

client = TestClient(app)


def assert_autocomplete(query: str, doc: str):
    response = client.get(query)
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == doc


def test_paris():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=paris", 'admin:osm:relation:71525')


def test_hotel_gabriel_paris():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=hotel gabriel paris", 'ta:poi:529918')


def test_mdph():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Direction de la Solidarité Départementale - MDPH",
                        'osm:relation:1672143')


def test_bruges():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Bruges", 'admin:osm:relation:562654')


# def test_mediateque():
#     assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Médiathèque Jules Verne", 'osm:node:2870807394')


def test_la_balme():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=La Balme-de-Sillingy", 'admin:osm:relation:103823')


def test_megeve():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Megève", 'admin:osm:relation:75312')


def test_saffre():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Saffré", 'admin:osm:relation:173715')
