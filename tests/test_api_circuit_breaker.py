import responses
import pytest
import re
from freezegun import freeze_time
from app import app
from apistar.test import TestClient
from idunn.blocks.wikipedia import WikipediaBreaker
from time import sleep

from .test_full import fake_all_blocks

@pytest.fixture(scope="module", autouse=True)
def breaker_test():
    """
    We define here settings specific to tests
    for the circuit_breaker in order to avoid
    any waste of time with real timeout and
    failmax
    """
    WikipediaBreaker.init_breaker()
    wiki_breaker = WikipediaBreaker.get_breaker()
    wiki_breaker.fail_max = 3
    wiki_breaker.reset_timeout = 1
    return wiki_breaker

def test_circuit_breaker_500(fake_all_blocks, breaker_test):
    """
    Test when the external service returns a
    HTTPError 500.
    Test that all possible blocks are correct even
    if the circuit is open.
    """
    client = TestClient(app)
    with responses.RequestsMock() as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=500)
        """
        We mock 40 calls to wikipedia while the max number
        of failure is 30, so we test that after 30 calls
        the circuit is open (i.e there are no more than 30
        calls sent).
        """
        breaker_test.close()

        for i in range(10):
            response = client.get(
                url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
            )

        assert response.status_code == 200

        assert 'open' == breaker_test.current_state
        assert len(rsps.calls) == 3

        resp = response.json()
        assert all(b['type'] != "wikipedia" for b in resp['blocks'])

        """
        After the timeout the circuit should be half-open.
        So one more external call should be done.
        """
        sleep(3)

        for i in range(10):
            response = client.get(
                url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
            )
        assert len(rsps.calls) == 4

def test_circuit_breaker_404(fake_all_blocks, breaker_test):
    """
    Same test as 'test_circuit_breaker_500' except
    that the external service returns this time an
    HTTPError 404.
    The circuit doesn't open on 404.
    Consequently we should observe the same number
    of calls.
    """
    client = TestClient(app)
    with responses.RequestsMock() as rsps:
        rsps.add('GET',
                re.compile('^https://.*\.wikipedia.org/'),
                status=404)
        """
        Even after more requests than the max number of
        failures of the circuit breaker the circuit should
        remained closed since the 404 is an exlude exception
        """
        breaker_test.close()

        for i in range(4):
            response = client.get(
               url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
            )

        assert 'closed' == breaker_test.current_state
        assert len(rsps.calls) == 4

        resp = response.json()
        assert all(b['type'] != "wikipedia" for b in resp['blocks'])
