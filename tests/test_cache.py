import responses
import re
from unittest import mock
from redis import Redis, RedisError
from app import app, settings
from fastapi.testclient import TestClient
from idunn.utils.redis import RedisWrapper
from functools import wraps
import pytest

# Required fixtures
from .test_wiki_ES import basket_ball_wiki_es
from .test_api_with_wiki import mock_wikipedia_response


@pytest.fixture(scope="function")
def cache_test_normal(redis):
    """
    We define here settings specific to the
    test of the Wikipedia/Wikidata cache
    """
    settings._settings["REDIS_URL"] = redis
    RedisWrapper._connection = None
    yield
    settings._settings["REDIS_URL"] = None
    RedisWrapper._connection = None


def test_wikipedia_cache(cache_test_normal, mock_wikipedia_response):
    """
    Test that Idunn stops external requests when
    answers are in the cache
    """
    client = TestClient(app)

    # We make a first request for the louvre museum POI
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
    resp = response.json()

    # One request requires 2 wikipedia API calls
    assert len(mock_wikipedia_response.calls) == 2
    assert any(b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks"))

    # We make another request to the same POI which should now be in the cache.
    # As a result no more Wikipedia call should be made.
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
    resp = response.json()

    assert len(mock_wikipedia_response.calls) == 2  # the same number of requests as before
    assert any(
        b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks")
    )  # we still have a wikipedia block


def test_wikidata_cache(cache_test_normal, basket_ball_wiki_es, monkeypatch):
    """
    We test the cache for the Wikidata ES
    """
    client = TestClient(app)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        # We mock all wikipedia requests since the information are expected to
        # be in the Wiki ES.
        rsps.add("GET", re.compile(r"^https://.*\.wikipedia.org/"), status=200)

        response = client.get(url="http://localhost/v1/pois/osm:way:7777777?lang=fr")

        assert response.status_code == 200
        resp = response.json()
        # We should have a "wikipedia" block in the answer.
        assert any(b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks"))

        with monkeypatch.context() as m:
            # Now that the "basket ball" request should be in the cache, we test
            # that the same request will not invoke the WikidataConnector.
            #
            # So we change the method used by the WikidataConnector by a fake
            # method to be sure the real method is not called.
            from idunn.datasources.wikidata import wikidata_es

            @wraps(wikidata_es.get_info)
            def fake_get_info():
                """
                Fake method for test

                This method should never be called
                """
                raise Exception

            m.setattr(wikidata_es, "get_info", fake_get_info)

            # We make 10 requests to the basket_ball POI and we should still
            # have the wikipedia block in the answer but without call to
            # wikidata neither wikipedia.
            #
            # Without the cache the request would fail in the "get_wiki_info()"
            # method.
            for _ in range(10):
                response = client.get(url="http://localhost/v1/pois/osm:way:7777777?lang=fr")
                resp = response.json()
                assert any(
                    b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks")
                )  # we still have the wikipedia block

            assert len(rsps.calls) == 0  # Wikipedia API has never been called


def test_wiki_cache_unavailable(cache_test_normal, mock_wikipedia_response):
    """
    Wikipedia should NOT be called if cache is enabled in settings,
    and redis is not reachable
    """

    def fake_get(*args):
        # A method 'get' for Redis,
        # that behaves as if redis is not available
        raise RedisError

    with mock.patch.object(Redis, "get", fake_get):
        client = TestClient(app)
        response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
        assert response.status_code == 200
        resp = response.json()
        assert len(mock_wikipedia_response.calls) == 0
        assert not any(b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks"))
