from apistar.test import TestClient
from freezegun import freeze_time
import pytest
import os
import re
import json
import responses
from .utils import override_settings
from idunn.api.places_list import PlacesQueryParam

from app import app, settings

@pytest.fixture(scope="function")
def kuzzle_test_normal():
    """
    We define here settings specific to tests.
    We define kuzzle address and port
    """
    with override_settings({'KUZZLE_CLUSTER_ADDRESS': 'localhost', 'KUZZLE_CLUSTER_PORT': '7512'}):
        yield

    # override_settings({'KUZZLE_CLUSTER_ADDRESS': 'localhost', 'KUZZLE_CLUSTER_PORT': '7512'})

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_kuzzle_event_ok(kuzzle_test_normal):
    """
    Check the result of events contained in bbox
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'kuzzle_event_response.json')
    with open(filepath, "r") as f:
        json_event = json.load(f)

    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('POST',
             re.compile(r'^http://localhost:7512/opendatasoft/events/'),
             status=200,
             json=json_event)


        response = client.get(
            url=f'http://localhost/v1/events?bbox=2.0667651,48.432533,2.9384989,49.0349191&raw_filter=bakery,*&size=5',
        )

        print(response.json())
        assert len(rsps.calls) == 1

        resp = response.json()
        firstEventData = resp['events'][0]

        assert firstEventData['id'] == '92106271'
        assert firstEventData['name'] == "Quand les livres expliquent la science"
        assert firstEventData['local_name'] == "Quand les livres expliquent la science"
        assert firstEventData['class_name'] is None
        assert firstEventData['subclass_name'] is None
        assert firstEventData['address']['name'] == 'Cité des Sciences et de l\'Industrie'
        assert firstEventData['address']['label'] == '30 Avenue Corentin Cariou, Paris'
        assert firstEventData['address']['city'] == 'Paris'
        assert firstEventData['blocks'][0]['type'] == 'event_opening_date'
        assert firstEventData['blocks'][1]['type'] == 'event_description'
        assert firstEventData['blocks'][2]['type'] == 'website'
        assert firstEventData['blocks'][3]['type'] == 'images'
        assert firstEventData['blocks'][0]['date_start'] == '2019-03-23T00:00:00.000Z'
        assert firstEventData['blocks'][3]['images'] == [
            {
              "url": "https://s2.qwant.com/thumbr/0x0/b/8/ad1bd2ff50021ff6a1239585cc9ccde31e70072299c3cc910da54f9e791f7c/.jpg?u=&q=0&b=1&p=0&a=0",
              "alt": "Quand les livres expliquent la science",
              "credits": "",
              "source_url": ""
            },
            {
              "url": "https://s2.qwant.com/thumbr/0x0/b/8/ad1bd2ff50021ff6a1239585cc9ccde31e70072299c3cc910da54f9e791f7c/.jpg?u=&q=0&b=1&p=0&a=0",
              "alt": "Quand les livres expliquent la science",
              "credits": "",
              "source_url": ""
            }
        ]


        """
        We check that there is no Wikipedia block
        in the answer
        """
        assert all(b['type'] != "wikipedia" for b in firstEventData['blocks'])

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_kuzzle_event_nok():
    """
    Check that an error is raised when kuzzle port and address not set
    """
    with pytest.raises(Exception):
        filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'kuzzle_event_response.json')
        with open(filepath, "r") as f:
            json_event = json.load(f)

        client = TestClient(app)
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            rsps.add('POST',
                 re.compile(r'^http://localhost:7512/opendatasoft/events/'),
                 status=200,
                 json=json_event)


            response = client.get(
                url=f'http://localhost/v1/events?bbox=2.0667651,48.432533,2.9384989,49.0349191&raw_filter=bakery,*&size=5',
            )

            # print(response.json())
            # assert len(rsps.calls) == 1

