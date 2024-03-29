import os

import pytest
from fastapi.testclient import TestClient

os.environ['IS_TEST'] = 'true'

from app import app

client = TestClient(app)


def assert_autocomplete(query: str, doc: str):
    response = client.get(query)
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'] == doc


def assert_places_list_datasource(query: str, datasource: str):
    response = client.get(query)
    assert response.status_code == 200
    assert len(response.json()['data']['result']['places']) > 0
    assert response.json()['data']['result']['places'][0]['id'][:2] == datasource[:2]


class TestAdmin:
    @pytest.mark.parametrize("query, expected_id", [
        ("paris", 'admin:osm:relation:71525'),
        ("Bruges", 'admin:osm:relation:105271'),
        ("La Balme-de-Sillingy", 'admin:osm:relation:103823'),
        ("Megève", 'admin:osm:relation:75312'),
        ("Saffré", 'admin:osm:relation:173715'),
    ])
    def test_city(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)

    @pytest.mark.parametrize("query, expected_id", [
        ("lyon 4e arrondissement", 'admin:osm:relation:18510'),
    ])
    def test_city_district(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)

    @pytest.mark.parametrize("query, expected_id", [
        ("vaise", 'admin:osm:relation:6531571'),
    ])
    def test_suburb(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)


class TestShouldCallTripadvisor:
    @pytest.mark.parametrize("query, expected_id", [
        ("hotel gabriel paris", 'ta:poi:529918'),
        ("hotel moliere", 'ta:poi:232545'),
    ])
    def test_when_hotel_category_is_detected(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)

    def test_when_poi_without_place_intention(self):
        assert_autocomplete("http://localhost:5000/v1/instant_answer?q=garden bistro", 'ta:poi:1509459')

    def test_when_poi_of_type_hotel_with_wikidataid(self):
        assert_autocomplete("http://localhost:5000/v1/instant_answer?q=Waldorf Astoria Versailles - Trianon Palace",
                            'ta:poi:229673')

    @pytest.mark.parametrize("query, expected_id", [
        ("café rive droite", 'ta:poi:1540773'),
        ("CiPASSO Bistrot", 'ta:poi:14121704'),
    ])
    def test_when_restaurant_without_place_intention(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)

    @pytest.mark.parametrize("query, expected_id", [
        ("CiPASSO Bistrot rome", 'ta:poi:14121704'),
    ])
    def test_when_restaurant_with_place_intention_outside_france(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)


class TestShouldCallPagesJaunes:
    def test_when_restaurant_with_france_place_intention(self):
        assert_autocomplete("http://localhost:5000/v1/instant_answer?q=garden bistro lyon", 'pj:58140933')

    def test_when_poi_with_place_in_france(self):
        assert_autocomplete("http://localhost:5000/v1/instant_answer?q=ecole maternelle jacques prevert orléans",
                            'pj:12359795')

    def test_when_cat_with_place_in_france(self):
        assert_places_list_datasource("http://localhost:5000/v1/instant_answer?q=spa paris&lang=fr", 'pj')


class TestShouldCallOSM:
    @pytest.mark.parametrize("query, expected_id", [
        ("tour eiffel", 'osm:way:5013364'),
        ("groupama stadium", 'osm:way:848361602'),
        ("Museo Ebraico di Bologna", 'osm:node:1704239999'),
    ])
    def test_when_poi_link_with_wikidata_id(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)

    @pytest.mark.parametrize("query, expected_id", [
        ("Direction de la Solidarité Départementale - MDPH", 'osm:relation:1672143'),
        ("Dipartimento di Filosofia e Comunicazione", 'osm:way:378227146')
    ])
    def test_fallback_osm(self, query, expected_id):
        assert_autocomplete(f"http://localhost:5000/v1/instant_answer?q={query}", expected_id)

