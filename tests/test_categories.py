import os
import json
import pytest
from app import app
from apistar.test import TestClient
from freezegun import freeze_time
from .test_api import load_poi

BBOX_PARIS="2.252876,48.819862,2.395707,48.891132"

def load_poi(file_name, mimir_client):
    """
    Load a json file in the elasticsearch and returns the corresponding POI id
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', file_name)
    with open(filepath, "r") as f:
        poi = json.load(f)
        poi_id = poi['id']
        mimir_client.index(index='munin_poi',
                        body=poi,
                        doc_type='poi',
                        id=poi_id,
                        refresh=True)

@pytest.fixture(autouse=True)
def load_all(mimir_client, init_indices):
    """
    fill elasticsearch with 4 POI:
        - 3 are in the BBOX_PARIS
        - 1 is not (patisserie)
    """
    load_poi('patisserie_peron.json', mimir_client)
    load_poi('orsay_museum.json', mimir_client)
    load_poi('blancs_manteaux.json', mimir_client)
    load_poi('louvre_museum.json', mimir_client)

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_bbox():
    """
        Test the bbox query:
        Query first all categories in fixtures with bbox that excludes the patisserie POI
        We should have 3 POI results: blancs_manteaux, orsay and louvre, but not patisserie_peron (not in bbox)
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places/_list?bbox={BBOX_PARIS}&raw_filter[]=(_any,bakery),(_any,museum),(_any,place_of_worship)'
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "places": [
            {
                'type': 'poi',
                'id': 'osm:way:63178753',
                'name': "Musee d'Orsay",
                'local_name': "Musée d'Orsay",
                'class_name': 'museum',
                'subclass_name': 'museum',
                'geometry': {'type': 'Point', 'coordinates': [2.3265827716099623, 48.859917803575875], 'center': [2.3265827716099623, 48.859917803575875]},
                'address': {'id': 'addr_poi:osm:way:63178753', 'name': "1 Rue de la Légion d'Honneur", 'housenumber': '1', 'postcode': '75007', 'label': "1 Rue de la Légion d'Honneur (Paris)", 'admin': None, 'street': {'id': 'street_poi:osm:way:63178753', 'name': "Rue de la Légion d'Honneur", 'label': "Rue de la Légion d'Honneur (Paris)", 'postcodes': ['75007']}, 'admins': [{'id': 'admin:osm:relation:2188567', 'label': "Quartier Saint-Thomas-d'Aquin (75007), Paris 7e Arrondissement, Paris, Île-de-France, France", 'name': "Quartier Saint-Thomas-d'Aquin", 'class_name': 10, 'postcodes': ['75007']}, {'id': 'admin:osm:relation:9521', 'label': 'Paris 7e Arrondissement (75007), Paris, Île-de-France, France', 'name': 'Paris 7e Arrondissement', 'class_name': 9, 'postcodes': ['75007']}, {'id': 'admin:osm:relation:7444', 'label': 'Paris (75000-75116), Île-de-France, France', 'name': 'Paris', 'class_name': 8, 'postcodes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116']}, {'id': 'admin:osm:relation:71525', 'label': 'Paris, Île-de-France, France', 'name': 'Paris', 'class_name': 6, 'postcodes': []}, {'id': 'admin:osm:relation:8649', 'label': 'Île-de-France, France', 'name': 'Île-de-France', 'class_name': 4, 'postcodes': []}, {'id': 'admin:osm:relation:2202162', 'label': 'France', 'name': 'France', 'class_name': 2, 'postcodes': []}]},
                'blocks': [{'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T21:45:00+02:00', 'seconds_before_next_transition': 40500, 'is_24_7': False, 'raw': 'Tu-Su 09:30-18:00; Th 09:30-21:45', 'days': [{'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'closed', 'opening_hours': []}, {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '21:45'}]}, {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}]}]
            },
            {
                'type': 'poi',
                'id': 'osm:way:55984117',
                'name': 'Église Notre-Dame-des-Blancs-Manteaux',
                'local_name': 'Église Notre-Dame-des-Blancs-Manteaux',
                'class_name': 'place_of_worship',
                'subclass_name': 'place_of_worship',
                'geometry': {'type': 'Point', 'coordinates': [2.3577366716253647, 48.858955519212905], 'center': [2.3577366716253647, 48.858955519212905]},
                'address': {'id': '4574400', 'name': 'Rue Aubriot', 'housenumber': None, 'postcode': '75004', 'label': 'Rue Aubriot (Paris)', 'admin': None, 'street': {'id': None, 'name': None, 'label': None, 'postcodes': None}, 'admins': [{'id': 'admin:osm:relation:2172741', 'label': 'Quartier Saint-Gervais (75004), Paris 4e Arrondissement, Paris, Île-de-France, France', 'name': 'Quartier Saint-Gervais', 'class_name': 10, 'postcodes': ['75004']}, {'id': 'admin:osm:relation:7444', 'label': 'Paris (75000-75116), Île-de-France, France', 'name': 'Paris', 'class_name': 8, 'postcodes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116']}, {'id': 'admin:osm:relation:71525', 'label': 'Paris, Île-de-France, France', 'name': 'Paris', 'class_name': 6, 'postcodes': []}, {'id': 'admin:osm:relation:8649', 'label': 'Île-de-France, France', 'name': 'Île-de-France', 'class_name': 4, 'postcodes': []}, {'id': 'admin:osm:relation:9597', 'label': 'Paris 4e Arrondissement (75004), Paris, Île-de-France, France', 'name': 'Paris 4e Arrondissement', 'class_name': 9, 'postcodes': ['75004']}, {'id': 'admin:osm:relation:2202162', 'label': 'France', 'name': 'France', 'class_name': 2, 'postcodes': []}]},
                'blocks': []
            },
            {
                'type': 'poi',
                'id': 'osm:relation:7515426',
                'name': 'Louvre Museum',
                'local_name': 'Musée du Louvre',
                'class_name': 'museum',
                'subclass_name': 'museum',
                'geometry': {'type': 'Point', 'coordinates': [2.338027583323689, 48.86114726113347], 'center': [2.338027583323689, 48.86114726113347]},
                'address': {'id': 'addr:2.338773;48.860861', 'name': '91A Rue de Rivoli', 'housenumber': '91A', 'postcode': '75001', 'label': '91A Rue de Rivoli (Paris)', 'admin': None, 'street': {'id': 'street:751018249S', 'name': 'Rue de Rivoli', 'label': 'Rue de Rivoli (Paris)', 'postcodes': ['75001']}, 'admins': [{'id': 'admin:osm:relation:2172740', 'label': "Quartier Saint-Germain-l'Auxerrois (75001), Paris 1er Arrondissement, Paris, Île-de-France, France", 'name': "Quartier Saint-Germain-l'Auxerrois", 'class_name': 10, 'postcodes': ['75001']}, {'id': 'admin:osm:relation:20727', 'label': 'Paris 1er Arrondissement (75001), Paris, Île-de-France, France', 'name': 'Paris 1er Arrondissement', 'class_name': 9, 'postcodes': ['75001']}, {'id': 'admin:osm:relation:8649', 'label': 'Île-de-France, France', 'name': 'Île-de-France', 'class_name': 4, 'postcodes': []}, {'id': 'admin:osm:relation:7444', 'label': 'Paris (75000-75116), Île-de-France, France', 'name': 'Paris', 'class_name': 8, 'postcodes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116']}, {'id': 'admin:osm:relation:71525', 'label': 'Paris, Île-de-France, France', 'name': 'Paris', 'class_name': 6, 'postcodes': []}, {'id': 'admin:osm:relation:2202162', 'label': 'France', 'name': 'France', 'class_name': 2, 'postcodes': []}]},
                'blocks': [{'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T18:00:00+02:00', 'seconds_before_next_transition': 27000, 'is_24_7': False, 'raw': 'Mo,Th,Sa,Su 09:00-18:00; We,Fr 09:00-21:45; Tu off; Jan 1,May 1,Dec 25: off', 'days': [{'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'open', 'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]}, {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'closed', 'opening_hours': []}, {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open', 'opening_hours': [{'beginning': '09:00', 'end': '21:45'}]}, {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open', 'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]}, {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open', 'opening_hours': [{'beginning': '09:00', 'end': '21:45'}]}, {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open', 'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]}, {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open', 'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]}]}]
            }
        ]
    }

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_size_list():
    """
        Test the bbox query with a list size=1:
        Same test as test_bbox but with a max list size of 1
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places/_list?bbox={BBOX_PARIS}&raw_filter[]=(_any,bakery),(_any,museum),(_any,place_of_worship)&size=1'
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "places": [
            {
                'type': 'poi',
                'id': 'osm:way:63178753',
                'name': "Musee d'Orsay",
                'local_name': "Musée d'Orsay",
                'class_name': 'museum',
                'subclass_name': 'museum',
                'geometry': {'type': 'Point', 'coordinates': [2.3265827716099623, 48.859917803575875], 'center': [2.3265827716099623, 48.859917803575875]},
                'address': {'id': 'addr_poi:osm:way:63178753', 'name': "1 Rue de la Légion d'Honneur", 'housenumber': '1', 'postcode': '75007', 'label': "1 Rue de la Légion d'Honneur (Paris)", 'admin': None, 'street': {'id': 'street_poi:osm:way:63178753', 'name': "Rue de la Légion d'Honneur", 'label': "Rue de la Légion d'Honneur (Paris)", 'postcodes': ['75007']}, 'admins': [{'id': 'admin:osm:relation:2188567', 'label': "Quartier Saint-Thomas-d'Aquin (75007), Paris 7e Arrondissement, Paris, Île-de-France, France", 'name': "Quartier Saint-Thomas-d'Aquin", 'class_name': 10, 'postcodes': ['75007']}, {'id': 'admin:osm:relation:9521', 'label': 'Paris 7e Arrondissement (75007), Paris, Île-de-France, France', 'name': 'Paris 7e Arrondissement', 'class_name': 9, 'postcodes': ['75007']}, {'id': 'admin:osm:relation:7444', 'label': 'Paris (75000-75116), Île-de-France, France', 'name': 'Paris', 'class_name': 8, 'postcodes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116']}, {'id': 'admin:osm:relation:71525', 'label': 'Paris, Île-de-France, France', 'name': 'Paris', 'class_name': 6, 'postcodes': []}, {'id': 'admin:osm:relation:8649', 'label': 'Île-de-France, France', 'name': 'Île-de-France', 'class_name': 4, 'postcodes': []}, {'id': 'admin:osm:relation:2202162', 'label': 'France', 'name': 'France', 'class_name': 2, 'postcodes': []}]},
                'blocks': [{'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T21:45:00+02:00', 'seconds_before_next_transition': 40500, 'is_24_7': False, 'raw': 'Tu-Su 09:30-18:00; Th 09:30-21:45', 'days': [{'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'closed', 'opening_hours': []}, {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '21:45'}]}, {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}, {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open', 'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}]}]
            }
        ]
    }

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_category():
    """
        Test the category query
    """
    client = TestClient(app)
    """
    Test the category filter:
        Query just one categorie (place_of_worship) in fixtures with bbox that excludes patisserie POI
        The result should contain only one POI: blancs_manteaux
    """
    response = client.get(
        url=f'http://localhost/v1/places/_list?bbox={BBOX_PARIS}&raw_filter[]=(_any,place_of_worship)'
    )

    assert response.status_code == 200

    resp = response.json()

    assert resp == {
        "places": [
            {
                'type': 'poi',
                'id': 'osm:way:55984117',
                'name': 'Église Notre-Dame-des-Blancs-Manteaux',
                'local_name': 'Église Notre-Dame-des-Blancs-Manteaux',
                'class_name': 'place_of_worship',
                'subclass_name': 'place_of_worship',
                'geometry': {'type': 'Point', 'coordinates': [2.3577366716253647, 48.858955519212905], 'center': [2.3577366716253647, 48.858955519212905]},
                'address': {'id': '4574400', 'name': 'Rue Aubriot', 'housenumber': None, 'postcode': '75004', 'label': 'Rue Aubriot (Paris)', 'admin': None, 'street': {'id': None, 'name': None, 'label': None, 'postcodes': None}, 'admins': [{'id': 'admin:osm:relation:2172741', 'label': 'Quartier Saint-Gervais (75004), Paris 4e Arrondissement, Paris, Île-de-France, France', 'name': 'Quartier Saint-Gervais', 'class_name': 10, 'postcodes': ['75004']}, {'id': 'admin:osm:relation:7444', 'label': 'Paris (75000-75116), Île-de-France, France', 'name': 'Paris', 'class_name': 8, 'postcodes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116']}, {'id': 'admin:osm:relation:71525', 'label': 'Paris, Île-de-France, France', 'name': 'Paris', 'class_name': 6, 'postcodes': []}, {'id': 'admin:osm:relation:8649', 'label': 'Île-de-France, France', 'name': 'Île-de-France', 'class_name': 4, 'postcodes': []}, {'id': 'admin:osm:relation:9597', 'label': 'Paris 4e Arrondissement (75004), Paris, Île-de-France, France', 'name': 'Paris 4e Arrondissement', 'class_name': 9, 'postcodes': ['75004']}, {'id': 'admin:osm:relation:2202162', 'label': 'France', 'name': 'France', 'class_name': 2, 'postcodes': []}]},
                'blocks': []
            }
        ]
    }




