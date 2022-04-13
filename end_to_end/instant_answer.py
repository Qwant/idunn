import os

from fastapi.testclient import TestClient

os.environ['IS_TEST'] = 'true'

from app import app

client = TestClient(app)


def test_paris():
    response = client.get("http://localhost:5000/v1/instant_answer?q=paris")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'admin:osm:relation:71525'


def test_hotel_gabriel_paris():
    response = client.get("http://localhost:5000/v1/instant_answer?q=hotel gabriel paris")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'ta:poi:529918'


def test_mdph():
    response = client.get("http://localhost:5000/v1/instant_answer?q=Direction de la Solidarité Départementale - MDPH")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'osm:relation:1672143'


def test_bruges():
    response = client.get("http://localhost:5000/v1/instant_answer?q=Bruges")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'admin:osm:relation:562654'


def test_mediateque():
    response = client.get("http://localhost:5000/v1/instant_answer?q=Médiathèque Jules Verne")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'osm:node:3693423611'


def test_la_balme():
    response = client.get("http://localhost:5000/v1/instant_answer?q=La Balme-de-Sillingy")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'admin:osm:relation:103823'


def test_megeve():
    response = client.get("http://localhost:5000/v1/instant_answer?q=Megève")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'admin:osm:relation:75312'


def test_saffre():
    response = client.get("http://localhost:5000/v1/instant_answer?q=Saffré")
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == 'admin:osm:relation:173715'





