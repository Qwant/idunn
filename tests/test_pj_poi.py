from apistar import TestClient
from unittest import mock
import json
import os

from app import app
from idunn.api import places

from .utils import enable_pj_source


def read_fixture(filename):
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'pj', filename)
    return json.load(open(filepath))


@enable_pj_source()
def test_pj_place():
    musee_picasso = read_fixture('musee_picasso.json')
    with mock.patch.object(places.pj_source.es, 'search',
        new=lambda *x,**y : {"hits": {"hits": [musee_picasso]}}
    ):
        client = TestClient(app)
        response = client.get(
            url=f'http://localhost/v1/places/pj:05360257?lang=fr',
        )

        assert response.status_code == 200
        resp = response.json()
        assert resp['id'] == 'pj:05360257'
        assert resp['name'] == 'Musée Picasso'
        assert resp['address']['label'] == '5 r Thorigny, 75003 Paris'
        assert resp['class_name'] == 'museum'
        assert resp['subclass_name'] == 'museum'
        assert resp['type'] == 'poi'
        assert resp['meta']['source'] == 'pagesjaunes'
        assert resp['geometry']['center'] == [2.362634, 48.859702]

        blocks = resp['blocks']
        assert blocks[0]['type'] == 'opening_hours'
        assert blocks[0]['raw'] == "Tu-Su 10:30-18:00"

        assert blocks[1]['type'] == 'phone'
        assert blocks[1]['url'] == 'tel:+33185560036'

        assert blocks[2]['blocks'][0]['blocks'][0]['wheelchair'] == 'yes'

        assert blocks[3]['type'] == 'website'
        assert blocks[3]['url'] == 'http://www.museepicassoparis.fr'

        assert blocks[4]['type'] == 'images'
        assert len(blocks[4]['images']) == 3
        assert blocks[4]['images'][0]['source_url'] == 'https://[VOIR_TOUTES_PHOTOS]'

        assert blocks[5]['type'] == 'grades'
        assert blocks[5]['total_grades_count'] == 8
        assert blocks[5]['global_grade'] == 4.
        assert blocks[5]['url'] == 'https://[VOIR_TOUS_AVIS]'


@enable_pj_source()
def test_pj_place_with_missing_data():
    musee_picasso_short = read_fixture('musee_picasso_short.json')
    with mock.patch.object(places.pj_source.es, 'search',
        new=lambda *x,**y : {"hits": {"hits": [musee_picasso_short]}}
    ):
        client = TestClient(app)
        response = client.get(
            url=f'http://localhost/v1/places/pj:05360257?lang=fr',
        )

        assert response.status_code == 200
        resp = response.json()
        assert resp['id'] == 'pj:05360257'
        assert resp['name'] == 'Musée Picasso'
        assert resp['address']['label'] == ''
        assert resp['class_name'] == 'museum'
        assert resp['subclass_name'] == 'museum'
        assert resp['type'] == 'poi'
        assert resp['meta']['source'] == 'pagesjaunes'
        assert resp['geometry']['center'] == [2.362634, 48.859702]
