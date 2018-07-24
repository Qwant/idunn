import responses
import pytest
import re
from freezegun import freeze_time
from app import app, settings
from apistar.test import TestClient
from idunn.blocks.wikipedia import WikipediaLimiter
from time import sleep

from .test_full import fake_all_blocks

@pytest.fixture(scope="function")
def limiter_test(redis):
    """
    We define here settings specific to tests
    for the rate limiter in order to avoid
    any waste of time
    """
    settings._settings['WIKI_API_RL_PERIOD'] = 5
    settings._settings['WIKI_API_RL_MAX_CALLS'] = 3
    settings._settings['WIKI_API_REDIS_URL'] = redis
    WikipediaLimiter._limiter = None
    wiki_limiter = WikipediaLimiter.init_limiter()
    yield
    settings._settings['WIKI_API_RL_PERIOD'] = 100
    settings._settings['WIKI_API_RL_MAX_CALLS'] = 1
    settings._settings['WIKI_API_REDIS_URL'] = None
    WikipediaLimiter._limiter = None

def test_rate_limiter_with_redis(fake_all_blocks, limiter_test):
    """
    Test that Idunn stops external requests when
    we are above the max rate
    """
    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200,
             json={"test": "test"}
        )
        """
        We mock 10 calls to wikipedia while the max number
        of calls is 3, so we test that after 3 calls
        no more calls are done
        """

        for i in range(10):
            response = client.get(
               url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
            )

        assert len(rsps.calls) == 3

        """
        Because of the fail of the last call,
        no wikipedia block should be in the
        answer
        """
        resp = response.json()
        assert all(b['type'] != "wikipedia" for b in resp['blocks'])

def test_rate_limiter_without_redis(fake_all_blocks):
    """
    Test that Idunn doesn't stop external requests when
    no redis has been set: 10 requests to Idunn should
    generate 10 requests to Wikipedia API
    """
    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200,
             json={"test": "test"}
        )

        for i in range(10):
            response = client.get(
               url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
            )

        assert len(rsps.calls) == 10
