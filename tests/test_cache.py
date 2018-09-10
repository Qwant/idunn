import responses
import pytest
import re
from time import sleep
from freezegun import freeze_time
from app import app, settings
from apistar.test import TestClient
from idunn.blocks.wikipedia import WikipediaCache
from .test_wiki_ES import basket_ball_wiki_es, basket_ball
from .test_api import louvre_museum
from .test_rate_limiter import mock_wikipedia
from functools import wraps
import pytest


@pytest.fixture(scope="function")
def cache_test_normal(redis):
    """
    We define here settings specific to the
    test of the Wikipedia/Wikidata cache
    """
    settings._settings['WIKI_API_REDIS_URL'] = redis
    WikipediaCache._connection = None
    yield
    settings._settings['WIKI_API_REDIS_URL'] = None
    WikipediaCache._connection = None


def test_wikipedia_cache(louvre_museum, cache_test_normal, mock_wikipedia):
    """
    Test that Idunn stops external requests when
    answers are in the cache
    """
    client = TestClient(app)

    """
    We make a first request for the louvre museum POI
    """
    response = client.get(
       url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
    )
    resp = response.json()
    """
    One request requires 2 wikipedia API calls
    """
    assert len(mock_wikipedia.calls) == 2
    assert any(b['type'] == "wikipedia" for b in resp['blocks'][2].get('blocks'))

    """
    We make another request to the same POI which
    should now be in the cache.
    As a result no more Wikipedia call should be
    made
    """
    response = client.get(
       url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
    )
    resp = response.json()

    assert len(mock_wikipedia.calls) == 2 # the same number of requests as before
    assert any(b['type'] == "wikipedia" for b in resp['blocks'][2].get('blocks')) # we still have a wikipedia block


def test_wikidata_cache(cache_test_normal, basket_ball, basket_ball_wiki_es, monkeypatch):
    """
    We test the cache for the Wikidata ES
    """
    client = TestClient(app)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        """
        We mock all wikipedia requests since
        the information are expected to be in
        the Wiki ES
        """
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200)

        response = client.get(
            url=f'http://localhost/v1/pois/{basket_ball}?lang=fr',
        )

        assert response.status_code == 200
        resp = response.json()
        """
        We should have a "wikipedia" block in the
        answer
        """
        assert any(b['type'] == "wikipedia" for b in resp['blocks'][2].get('blocks'))

        with monkeypatch.context() as m:
            """
            Now that the "basket ball" request should be
            in the cache, we test that the same request
            will not invoke the WikidataConnector

            So we change the method used by the WikidataConnector
            by a fake method to be sure the real method is not
            called
            """
            from idunn.blocks.wikipedia import WikidataConnector

            @wraps(WikidataConnector.get_wiki_info)
            def fake_get_wiki_info():
                """
                Fake method for test

                This method should never be called
                """
                raise Exception

            m.setattr(WikidataConnector, "get_wiki_info", fake_get_wiki_info)

            """
            We make 10 requests to the basket_ball POI
            and we should still have the wikipedia block
            in the answer but without call to wikidata
            neither wikipedia

            Without the cache the request would fail
            in the "get_wiki_info()" method
            """
            for i in range(10):
                response = client.get(
                    url=f'http://localhost/v1/pois/{basket_ball}?lang=fr',
                )
                resp = response.json()
                assert any(b['type'] == "wikipedia" for b in resp['blocks'][2].get('blocks')) # we still have the wikipedia block

            assert len(rsps.calls) == 0 # Wikipedia API has never been called
