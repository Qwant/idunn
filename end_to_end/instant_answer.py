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


def test_admin_paris():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=paris", 'admin:osm:relation:71525')


def test_admin_bruges():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Bruges", 'admin:osm:relation:562654')


def test_admin_la_balme():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=La Balme-de-Sillingy", 'admin:osm:relation:103823')


def test_admin_megeve():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Megève", 'admin:osm:relation:75312')


def test_admin_saffre():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Saffré", 'admin:osm:relation:173715')


def test_mdph():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Direction de la Solidarité Départementale - MDPH",
                        'osm:relation:1672143')


def test_hotel_should_call_tripadvisor_when_hotel_category_is_detected():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=hotel gabriel paris", 'ta:poi:529918')


def test_restaurant_with_france_place_intention_should_call_pagesjaunes_for_poi():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=garden bistro lyon", 'pj:58140933')


def test_poi_without_place_intention_should_call_tripadvisor_when_found():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=garden bistro", 'ta:poi:1509459')


def test_restaurant_without_place_intention_should_call_tripadvisor_when_found():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=café rive droite", 'ta:poi:1540773')

#TODO to fix
def test_osm_for_famous_poi():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=tour eiffel", 'osm:way:5013364')


def test_attraction_should_call_tripadvisor():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=groupama stadium", 'ta:poi:9769104')


def test_fallback_osm():
    assert_autocomplete("http://localhost:5000/v1/instant_answer?q=ecole maternel jacques prevert orléans", 'osm:way:810143256')
