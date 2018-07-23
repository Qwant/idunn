from apistar.test import TestClient
from freezegun import freeze_time
from app import app, settings
import pytest
import os
import re
import json
from .test_api import load_poi
import responses

@pytest.fixture(scope="session")
def basket_ball_wiki_es(wiki_client, init_indices):
    """
    fill the elasticsearch WIKI_ES with a POI of basket ball
    """
    filepath = os.path.join(os.path.dirname(__file__), 'fixtures', 'basket_ball_wiki_es.json')
    with open(filepath, "r") as f:
        poi = json.load(f)
        poi_id = poi['id']
        wiki_client.index(index='wikidata_fr',
                        body=poi,
                        doc_type='wikipedia',
                        id=poi_id,
                        refresh=True)
        return poi_id

@pytest.fixture(scope="session")
def basket_ball(mimir_client):
    """
    fill elasticsearch with a fake POI of basket ball
    """
    return load_poi('basket_ball.json', mimir_client)

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_undefined_WIKI_ES(basket_ball):
    """
    Check that when the WIKI_ES variable is not set
    a Wikipedia call is observed
    """
    from idunn.blocks.wikipedia import WikidataConnector
    client = TestClient(app)
    WikidataConnector._wiki_es = None
    wiki_es_ip = settings['WIKI_ES'] # temporary variable to store the ip of WIKI_ES to reset it after the test
    settings._settings['WIKI_ES'] = None
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200,
             json={"test": "test"})

        for i in range(10):
            response = client.get(
                url=f'http://localhost/v1/pois/{basket_ball}?lang=fr',
            )

        assert len(rsps.calls) == 10
    settings._settings['WIKI_ES'] = wiki_es_ip # put back the correct ip for next tests

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_POI_not_in_WIKI_ES(basket_ball, basket_ball_wiki_es):
    """
    Test that when the POI requested is not in WIKI_ES
    no call to Wikipedia is observed
    """
    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200)

        response = client.get(
                url=f'http://localhost/v1/pois/osm:way:7777777?lang=fr',
        )

        assert response.status_code == 200

        assert len(rsps.calls) == 0


@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_no_lang_WIKI_ES(basket_ball, basket_ball_wiki_es):
    """
    Test that when we don't have the lang available in the index
    we call Wikipedia API
    """
    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200,
             json={"test": "test"})

        """
        We make a request in russian language ("ru")
        """
        response = client.get(
            url=f'http://localhost/v1/pois/{basket_ball}?lang=ru',
        )

        assert len(rsps.calls) == 1

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_basket_ball(basket_ball, basket_ball_wiki_es):
    """
    Check that the wikipedia block contains the correct
    information about a POI that is in the WIKI_ES.
    """
    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200)

        response = client.get(
            url=f'http://localhost/v1/pois/{basket_ball}?lang=fr',
        )

        assert response.status_code == 200

        resp = response.json()

        assert resp['blocks'][2].get('blocks')[0] == {
            'type': 'wikipedia',
            'url': 'https://fr.wikipedia.org/wiki/Pleyber-Christ_Basket_Club',
            'title': 'Pleyber-Christ Basket Club',
            'description': "Le Pleyber-Christ Basket Club est un club français de basket-ball dont la section senior féminine a accédé jusqu'au championnat professionnel de Ligue 2 (2e division nationale), performance remarquée pour un village de 3000 habitants. Le club est basé dans la ville de Pleyber-Christ. Il accueille aussi de jeunes joueuses depuis 2010 dans son centre de formation situé à Pleyber-Christ."
        }

        """
        Even after 10 requests for a POI in the WIKI_ES
        we should not observe any call to the Wikipedia
        API
        """
        for i in range(10):
            response = client.get(
                url=f'http://localhost/v1/pois/{basket_ball}?lang=fr',
            )

        assert len(rsps.calls) == 0
