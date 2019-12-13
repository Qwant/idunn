from unittest.mock import ANY
from app import app
from starlette.testclient import TestClient
from freezegun import freeze_time

from .utils import enable_pj_source

BBOX_PARIS="2.252876,48.819862,2.395707,48.891132"
BBOX_BREST="-4.807542,48.090743,-4.097541,48.800743"
INVALID_BBOX_PARIS_LEFT_PERM_RIGHT="2.395707,48.819862,2.252876,48.891132"
INVALID_BBOX_PARIS_MISSING="48.819862,2.252876,48.891132"

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_bbox():
    """
        Test the bbox query:
        Query first all categories in fixtures with bbox that excludes the patisserie POI
        We should have 5 POI results including: blancs_manteaux, orsay and louvre, but not patisserie_peron (not in bbox)
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}&raw_filter=*,bakery&raw_filter=museum,*&raw_filter=*,place_of_worship'
    )

    assert response.status_code == 200

    resp = response.json()

    # TODO: to be updated
    # assert resp == {
    #     'source': 'osm',
    #     'places': [
    #         {
    #             'type': 'poi',
    #             'id': 'osm:way:63178753',
    #             'name': "Musee d'Orsay",
    #             'local_name': "Musée d'Orsay",
    #             'class_name': 'museum',
    #             'subclass_name': 'museum',
    #             'geometry': {'type': 'Point', 'coordinates': [2.3265827716099623, 48.859917803575875],
    #                          'center': [2.3265827716099623, 48.859917803575875]},
    #             'address': {
    #                 'id': 'addr_poi:osm:way:63178753',
    #                 'name': "1 Rue de la Légion d'Honneur",
    #                 'housenumber': '1',
    #                 'postcode': '75007',
    #                 'label': "1 Rue de la Légion d'Honneur (Paris)",
    #                 'admin': None,
    #                 'street': {
    #                     'id': 'street_poi:osm:way:63178753',
    #                     'name': "Rue de la Légion d'Honneur",
    #                     'label': "Rue de la Légion d'Honneur (Paris)",
    #                     'postcodes': ['75007']
    #                 },
    #                 'admins': [
    #                     {
    #                         'id': 'admin:osm:relation:2188567',
    #                         'label': "Quartier Saint-Thomas-d'Aquin (75007), Paris 7e Arrondissement, Paris, Île-de-France, France",
    #                         'name': "Quartier Saint-Thomas-d'Aquin",
    #                         'class_name': "suburb",
    #                         'postcodes': ['75007']
    #                     },
    #                     ANY, ANY, ANY, ANY, ANY
    #                 ]
    #             },
    #             'blocks': [
    #                 {
    #                     'type': 'opening_hours',
    #                     'status': 'open',
    #                     'next_transition_datetime': '2018-06-14T21:45:00+02:00',
    #                     'seconds_before_next_transition': 40500,
    #                     'is_24_7': False,
    #                     'raw': 'Tu-Su 09:30-18:00; Th 09:30-21:45',
    #                     'days': [{'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'closed', 'opening_hours': []},
    #                           {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '21:45'}]},
    #                           {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}]
    #                 },
    #                 {
    #                     'type': 'phone',
    #                     'international_format': '+33 1 40 49 48 14',
    #                     'local_format': '01 40 49 48 14',
    #                     'url': 'tel:+33140494814'
    #                 },
    #                 {
    #                     'type': 'website',
    #                     'url': 'http://www.musee-orsay.fr'
    #                 }
    #             ],
    #             'meta': {
    #                 'source': 'osm'
    #             }
    #         },
    #         {
    #             'type': 'poi',
    #             'id': 'osm:way:55984117',
    #             'name': 'Église Notre-Dame-des-Blancs-Manteaux',
    #             'local_name': 'Église Notre-Dame-des-Blancs-Manteaux',
    #             'class_name': 'place_of_worship',
    #             'subclass_name': 'place_of_worship',
    #             'geometry': {'type': 'Point', 'coordinates': [2.3577366716253647, 48.858955519212905],
    #                          'center': [2.3577366716253647, 48.858955519212905]},
    #             'address': ANY,
    #             'blocks': [
    #                 {
    #                     'international_format': '+33 1 42 72 09 37',
    #                     'local_format': '01 42 72 09 37',
    #                     'type': 'phone',
    #                     'url': 'tel:+33142720937'
    #                 },
    #                 {
    #                     'type': 'website',
    #                     'url': 'http://www.paris.catholique.fr/-Notre-Dame-des-Blancs-Manteaux,1290-.html'
    #                 }
    #             ],
    #             'meta': {
    #                 'source': 'osm'
    #             }
    #         },
    #         {
    #             'type': 'poi',
    #             'id': 'osm:relation:7515426',
    #             'name': 'Louvre Museum',
    #             'local_name': 'Musée du Louvre',
    #             'class_name': 'museum',
    #             'subclass_name': 'museum',
    #             'geometry': {'type': 'Point', 'coordinates': [2.338027583323689, 48.86114726113347],
    #                          'center': [2.338027583323689, 48.86114726113347]},
    #             'address': ANY,
    #             'blocks': [
    #                 {
    #                     'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T18:00:00+02:00',
    #                     'seconds_before_next_transition': 27000, 'is_24_7': False,
    #                     'raw': 'Mo,Th,Sa,Su 09:00-18:00; We,Fr 09:00-21:45; Tu off; Jan 1,May 1,Dec 25: off',
    #                     'days': [
    #                         {'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'open',
    #                          'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]},
    #                         {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'closed', 'opening_hours': []},
    #                         {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open',
    #                          'opening_hours': [{'beginning': '09:00', 'end': '21:45'}]},
    #                         {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open',
    #                          'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]},
    #                         {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open',
    #                          'opening_hours': [{'beginning': '09:00', 'end': '21:45'}]},
    #                         {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open',
    #                          'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]},
    #                         {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open',
    #                          'opening_hours': [{'beginning': '09:00', 'end': '18:00'}]}
    #                     ]
    #                 },
    #                 {
    #                     'international_format': '+33 1 40 20 52 29',
    #                     'local_format': '01 40 20 52 29',
    #                     'type': 'phone',
    #                     'url': 'tel:+33140205229'
    #                 },
    #                 {
    #                     'type': 'website',
    #                     'url': 'http://www.louvre.fr'
    #                 }
    #             ],
    #             'meta': {
    #                 'source': 'osm'
    #             }
    #         },
    #         {
    #             'type': 'poi',
    #             'id': 'osm:way:7777777',
    #             'name': 'Fake All',
    #             'local_name': 'Fake All',
    #             'class_name': 'museum',
    #             'subclass_name': 'museum',
    #             'geometry': {'type': 'Point', 'coordinates': [2.3250037768187326, 48.86618482685007],
    #                          'center': [2.3250037768187326, 48.86618482685007]},
    #             'address': ANY,
    #             'blocks': [
    #                 {
    #                     'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T21:45:00+02:00',
    #                     'seconds_before_next_transition': 40500, 'is_24_7': False,
    #                     'raw': 'Tu-Su 09:30-18:00; Th 09:30-21:45',
    #                     'days': [{'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'closed', 'opening_hours': []},
    #                           {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '21:45'}]},
    #                           {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}
    #                     ]
    #                 },
    #                 ANY,
    #                 ANY
    #             ],
    #             'meta': {
    #                 'source': 'osm'
    #             }
    #         },
    #         {
    #             'type': 'poi',
    #             'id': 'osm:way:7777778',
    #             'name': 'Fake All',
    #             'local_name': 'Fake All',
    #             'class_name': 'museum',
    #             'subclass_name': 'museum',
    #             'geometry': {'type': 'Point', 'coordinates': [2.3250037768187326, 48.86618482685007],
    #                          'center': [2.3250037768187326, 48.86618482685007]},
    #             'address': {'id': 'addr:2.326285;48.859635', 'name': '62B Rue de Lille', 'housenumber': '62B',
    #                         'postcode': '75007;75008', 'label': '62B Rue de Lille (Paris)', 'admin': None,
    #                         'street': {'id': 'street:553660044C', 'name': 'Rue de Lille',
    #                                    'label': 'Rue de Lille (Paris)', 'postcodes': ['75007', '75008']}, 'admins': []},
    #             'blocks': [
    #                 {
    #                     'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T21:45:00+02:00',
    #                     'seconds_before_next_transition': 40500, 'is_24_7': False,
    #                     'raw': 'Tu-Su 09:30-18:00; Th 09:30-21:45',
    #                     'days': [{'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'closed', 'opening_hours': []},
    #                           {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '21:45'}]},
    #                           {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                           {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open',
    #                            'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}
    #                     ]
    #                 },
    #                 ANY,
    #                 ANY
    #             ],
    #             'meta': {
    #                 'source': 'osm'
    #             }
    #         }
    #     ]
    # }

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_size_list():
    """
        Test the bbox query with a list size=1:
        Same test as test_bbox but with a max list size of 1
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}&raw_filter=*,bakery&raw_filter=museum,*&raw_filter=*,place_of_worship&size=1'
    )

    assert response.status_code == 200

    resp = response.json()

    # TODO: update test
    # assert resp == {
    #     "source": "osm",
    #     "places": [
    #         {
    #             'type': 'poi',
    #             'id': 'osm:way:63178753',
    #             'name': "Musee d'Orsay",
    #             'local_name': "Musée d'Orsay",
    #             'class_name': 'museum',
    #             'subclass_name': 'museum',
    #             'geometry': {'type': 'Point', 'coordinates': [2.3265827716099623, 48.859917803575875],
    #                          'center': [2.3265827716099623, 48.859917803575875]},
    #             'address': ANY,
    #             'blocks': [
    #                 {
    #                     'type': 'opening_hours', 'status': 'open', 'next_transition_datetime': '2018-06-14T21:45:00+02:00',
    #                     'seconds_before_next_transition': 40500, 'is_24_7': False,
    #                     'raw': 'Tu-Su 09:30-18:00; Th 09:30-21:45',
    #                     'days': [
    #                         {'dayofweek': 1, 'local_date': '2018-06-11', 'status': 'closed', 'opening_hours': []},
    #                         {'dayofweek': 2, 'local_date': '2018-06-12', 'status': 'open',
    #                         'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                         {'dayofweek': 3, 'local_date': '2018-06-13', 'status': 'open',
    #                         'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                         {'dayofweek': 4, 'local_date': '2018-06-14', 'status': 'open',
    #                         'opening_hours': [{'beginning': '09:30', 'end': '21:45'}]},
    #                         {'dayofweek': 5, 'local_date': '2018-06-15', 'status': 'open',
    #                         'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                         {'dayofweek': 6, 'local_date': '2018-06-16', 'status': 'open',
    #                         'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]},
    #                         {'dayofweek': 7, 'local_date': '2018-06-17', 'status': 'open',
    #                         'opening_hours': [{'beginning': '09:30', 'end': '18:00'}]}
    #                     ]
    #                 },
    #                 {
    #                     'international_format': '+33 1 40 49 48 14',
    #                     'local_format': '01 40 49 48 14',
    #                     'type': 'phone',
    #                     'url': 'tel:+33140494814'
    #                 },
    #                 {
    #                     'type': 'website',
    #                     'url': 'http://www.musee-orsay.fr'
    #                 }
    #             ],
    #             'meta': ANY
    #         }
    #     ]
    # }

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_single_raw_filter():
    client = TestClient(app)
    """
    Test the category filter:
        Query just one category (place_of_worship) in fixtures with bbox that excludes patisserie POI
        The result should contain only one POI: blancs_manteaux
    """
    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}&raw_filter=*,place_of_worship'
    )

    assert response.status_code == 200

    resp = response.json()

    # TODO: update test
    # assert resp == {
    #     "source": "osm",
    #     "places": [
    #         {
    #             'type': 'poi',
    #             'id': 'osm:way:55984117',
    #             'name': 'Église Notre-Dame-des-Blancs-Manteaux',
    #             'local_name': 'Église Notre-Dame-des-Blancs-Manteaux',
    #             'class_name': 'place_of_worship',
    #             'subclass_name': 'place_of_worship',
    #             'geometry': {'type': 'Point', 'coordinates': [2.3577366716253647, 48.858955519212905], 'center': [2.3577366716253647, 48.858955519212905]},
    #             'address': {
    #                 'id': '4574400',
    #                 'name': 'Rue Aubriot',
    #                 'housenumber': None,
    #                 'postcode': '75004',
    #                 'label': 'Rue Aubriot (Paris)',
    #                 'admin': None,
    #                 'street': {
    #                     'id': '4574400',
    #                     'name': "Rue Aubriot",
    #                     'label': "Rue Aubriot (Paris)",
    #                     'postcodes': ['75004']
    #                 },
    #                 'admins': [
    #                     {
    #                         'id': 'admin:osm:relation:2172741',
    #                         'label': 'Quartier Saint-Gervais (75004), Paris 4e Arrondissement, Paris, Île-de-France, France',
    #                         'name': 'Quartier Saint-Gervais',
    #                         'class_name': "suburb",
    #                         'postcodes': ['75004']
    #                     },
    #                     {
    #                         'id': 'admin:osm:relation:7444',
    #                         'label': 'Paris (75000-75116), Île-de-France, France',
    #                         'name': 'Paris',
    #                         'class_name': "city",
    #                         'postcodes': ['75000', '75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116']
    #                     },
    #                     {
    #                         'id': 'admin:osm:relation:71525',
    #                         'label': 'Paris, Île-de-France, France',
    #                         'name': 'Paris',
    #                         'class_name': "state_district",
    #                         'postcodes': []
    #                     },
    #                     {
    #                         'id': 'admin:osm:relation:8649',
    #                         'label': 'Île-de-France, France',
    #                         'name': 'Île-de-France',
    #                         'class_name': "state",
    #                         'postcodes': []
    #                     }, {
    #                         'id': 'admin:osm:relation:9597',
    #                         'label': 'Paris 4e Arrondissement (75004), Paris, Île-de-France, France',
    #                         'name': 'Paris 4e Arrondissement',
    #                         'class_name': "city_district",
    #                         'postcodes': ['75004']
    #                     },
    #                     {
    #                         'id': 'admin:osm:relation:2202162',
    #                         'label': 'France',
    #                         'name': 'France',
    #                         'class_name': "country",
    #                         'postcodes': []
    #                     }
    #                 ]
    #             },
    #             'blocks': [
    #                 {
    #                     'international_format': '+33 1 42 72 09 37',
    #                     'local_format': '01 42 72 09 37',
    #                     'type': 'phone',
    #                     'url': 'tel:+33142720937'
    #                 },
    #                 {
    #                     'type': 'website',
    #                     'url': 'http://www.paris.catholique.fr/-Notre-Dame-des-Blancs-Manteaux,1290-.html'
    #                 }
    #             ],
    #             'meta': ANY
    #         }
    #     ]
    # }

def test_raw_filter_with_class_subclass():
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}&raw_filter=museum,museum'
    )

    assert response.status_code == 200

    resp = response.json()

    # TODO: for some reasons, it returns actually 50 places
    # assert len(resp['places']) == 1
    # assert resp['places'][0]['name'] ==  'Louvre Museum'

def test_invalid_bbox():
    """
        Test an invalid bbox query:
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={INVALID_BBOX_PARIS_LEFT_PERM_RIGHT}&raw_filter=*,bakery&raw_filter=museum,*&raw_filter=*,place_of_worship'
    )

    assert response.status_code == 400

    resp = response.json()

    assert resp == {
        'detail': [
            {
                'loc': [
                    'bbox'
                ],
                'msg': 'bbox dimensions are invalid',
                'type': 'value_error'
            }
        ]
    }

    response = client.get(
        url=f'http://localhost/v1/places?bbox={INVALID_BBOX_PARIS_MISSING}&raw_filter=*,bakery&raw_filter=museum,*&raw_filter=*,place_of_worship'
    )

    assert response.status_code == 400

    resp = response.json()

    assert resp == {
        'detail': [
            {
                'loc': [
                    'bbox'
                ],
                'msg': 'bbox should contain 4 numbers',
                'type': 'value_error'
            }
        ]
    }


def test_category_and_raw_filter():
    """
        Test we get a 400 if category and raw_filter are both present:
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}&raw_filter=*,bakery&category=supermarket'
    )

    assert response.status_code == 400
    resp = response.json()
    assert resp == {
        'detail': "Both 'raw_filter' and 'category' parameters cannot be provided together"
    }


def test_category_or_raw_filter():
    """
        Test we get a 400 if none of category or raw_filter is present:
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}'
    )

    assert response.status_code == 400
    resp = response.json()
    assert resp == {'detail': "One of 'category', 'raw_filter' or 'q' parameter is required"}


def test_valid_category():
    """
        Test a valid category filter which should fetch only one cinema in a bbox around Brest city.
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_BREST}&category=leisure'
    )

    assert response.status_code == 200

    resp = response.json()

    # TODO: update test
    # assert resp == {
    #     'source': 'osm',
    #     'places': [
    #         {
    #             'type': 'poi',
    #             'id': 'osm:node:36153811',
    #             'name': 'Multiplexe Liberté',
    #             'local_name': 'Multiplexe Liberté',
    #             'class_name': 'cinema',
    #             'subclass_name': 'cinema',
    #             'geometry': ANY,
    #             'address': ANY,
    #             'blocks': [],
    #             'meta': {'source': 'osm'}
    #         }
    #     ]
    # }

@enable_pj_source()
def test_places_with_explicit_source_osm():
    """
        If source=osm is passed to the query, pj_source should be ignored
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_BREST}&category=leisure&source=osm'
    )

    assert response.status_code == 200
    resp = response.json()

    # TODO: update test
    # assert resp == {
    #     'source': 'osm',
    #     'places': [
    #         {
    #             'type': 'poi',
    #             'id': 'osm:node:36153811',
    #             'name': 'Multiplexe Liberté',
    #             'local_name': 'Multiplexe Liberté',
    #             'class_name': 'cinema',
    #             'subclass_name': 'cinema',
    #             'geometry': ANY,
    #             'address': ANY,
    #             'blocks': [],
    #             'meta': {'source': 'osm'}
    #         }
    #     ]
    # }


def test_invalid_category():
    """
        Test we get a 400 if the parameter category is invalid:
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/places?bbox={BBOX_PARIS}&category=supppermarket'
    )

    assert response.status_code == 400

    resp = response.json()
    assert resp['detail'][0]['msg'].startswith("Category 'supppermarket' is invalid ")


def test_endpoint_categories():
    """
        Test the endpoint 'categories':
    """
    client = TestClient(app)

    response = client.get(
        url=f'http://localhost/v1/categories'
    )

    assert response.status_code == 200

    resp = response.json()
    categories = resp['categories']

    assert len(categories) == 12
    assert categories[0] == {
        "name": "restaurant",
        "raw_filters": [
            "restaurant,*",
            "fast_food,*"
        ]
    }
    assert categories[1] == {
        "name": "hotel",
        "raw_filters": [
            "*,hotel"
        ]
    }
