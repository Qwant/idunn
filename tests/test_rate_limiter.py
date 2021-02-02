# pylint: disable = line-too-long, redefined-outer-name, unused-argument, unused-import

import responses
import pytest
import re
from freezegun import freeze_time
from app import app, settings
from fastapi.testclient import TestClient
from idunn.blocks.wikipedia import WikipediaSession
from idunn.utils.redis import RedisWrapper
from .utils import override_settings
from .test_api_with_wiki import mock_wikipedia_response

from redis import RedisError
from redis_rate_limit import RateLimiter
from functools import wraps


@pytest.fixture(scope="function")
def disable_wikipedia_cache():
    RedisWrapper.disable()
    yield
    RedisWrapper._connection = None  # pylint: disable = protected-access


@pytest.fixture(scope="function")
def limiter_test_normal(redis, disable_wikipedia_cache):
    """
    We define here settings specific to tests.
    We define low max calls limits to avoid
    too large number of requests made
    """
    # pylint: disable = protected-access
    with override_settings(
        {"WIKI_API_RL_PERIOD": 5, "WIKI_API_RL_MAX_CALLS": 6, "REDIS_URL": redis}
    ):
        # To force settings overriding we need to set to None the limiter
        WikipediaSession._rate_limiter = None
        yield
    WikipediaSession._rate_limiter = None


@pytest.fixture(scope="function")
def limiter_test_interruption(redis, disable_wikipedia_cache):
    """
    In the 'Redis interruption' test below
    we made more requests than the limits
    allowed by the fixture 'limiter_test_normal'
    So we need another specific fixture.
    """
    # pylint: disable = protected-access
    with override_settings(
        {"WIKI_API_RL_PERIOD": 5, "WIKI_API_RL_MAX_CALLS": 100, "REDIS_URL": redis}
    ):
        WikipediaSession._rate_limiter = None
        yield
    WikipediaSession._rate_limiter = None


def test_rate_limiter_with_redis(limiter_test_normal, mock_wikipedia_response):
    """
    Test that Idunn stops external requests when
    we are above the max rate

    We mock 5 calls to wikipedia while the max number
    of calls is 3*2, so we test that after 3 calls
    no more calls are done
    """
    client = TestClient(app)

    for _ in range(3):
        response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
        resp = response.json()
        assert any(b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks"))

    for _ in range(2):
        response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
        resp = response.json()
        assert all(b["type"] != "wikipedia" for b in resp["blocks"][2].get("blocks"))

    assert len(mock_wikipedia_response.calls) == 6


def test_rate_limiter_without_redis():
    """
    Test that Idunn doesn't stop external requests when
    no redis has been set: 10 requests to Idunn should
    generate 10 requests to Wikipedia API
    """
    client = TestClient(app)

    with responses.RequestsMock() as rsps:
        rsps.add(
            "GET", re.compile(r"^https://.*\.wikipedia.org/"), status=200, json={"test": "test"}
        )
        for _ in range(10):
            client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")

        assert len(rsps.calls) == 10


def restart_wiki_redis(docker_services):
    """
    Because docker services ports are
    dynamically chosen when the service starts
    we have to get the new port of the service.
    """
    # pylint: disable = protected-access
    docker_services.start("wiki_redis")
    # We have to remove the previous port of the redis service which has been
    # stored in the dict '_services' before to get the new one.
    del docker_services._services["wiki_redis"]
    port = docker_services.port_for("wiki_redis", 6379)
    url = f"{docker_services.docker_ip}:{port}"
    settings._settings["REDIS_URL"] = url
    WikipediaSession._rate_limiter = None


def test_rate_limiter_with_redisError(
    limiter_test_interruption, mock_wikipedia_response, monkeypatch
):
    """
    Test that Idunn stops returning the wikipedia block
    when not enough space remains on the disk for the redis
    database used by the limiter.

    Also when the redis service comes back, Idunn should returns
    the wikipedia block again.
    """

    client = TestClient(app)

    # First we make a successful call before "stopping" redis.
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")

    assert response.status_code == 200
    resp = response.json()
    # Here the redis is on so the answer should contain the wikipedia block.
    assert any(b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks"))

    with monkeypatch.context() as m:

        @wraps(RateLimiter.limit)
        def fake_limit(*args, **kwargs):
            """
            Raises a RedisError to simulate a lack of
            space on the disk
            """
            raise RedisError

        # Now we substitute the limit function with our fake_limit.
        m.setattr(RateLimiter, "limit", fake_limit)

        client = TestClient(app)
        response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")

        assert response.status_code == 200
        resp = response.json()
        # No wikipedia block should be in the answer.
        assert any(b["type"] != "wikipedia" for b in resp["blocks"][2].get("blocks"))

    # Now that the redis "came back", we are expecting a correct answer from
    # Idunn.
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")

    assert response.status_code == 200
    resp = response.json()
    # Here the redis is on so the answer should contain the wikipedia block
    assert any(b["type"] == "wikipedia" for b in resp["blocks"][2].get("blocks"))


@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_rate_limiter_with_redis_interruption(
    docker_services, mock_wikipedia_response, limiter_test_interruption
):
    """
    Test that Idunn isn't impacted by any Redis interruption:
    If Redis service stops then the wikipedia block should not be returned.
    And when Redis restarts the wikipedia block should be returned again

    This test has 3 steps:
        * A: redis is up: we have the wiki block
        * B: redis is down: no wiki block
        * C: redis is up again: we have the wiki block again
    """
    client = TestClient(app)

    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    resp = response.json()

    # A - Before Redis interruption we check the answer is correct
    assert resp["id"] == "osm:relation:7515426"
    assert resp["name"] == "Museo del Louvre"
    assert resp["local_name"] == "Musée du Louvre"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["blocks"][2].get("blocks")[0] == {
        "type": "wikipedia",
        "url": "https://es.wikipedia.org/wiki/Museo_del_Louvre",
        "title": "Museo del Louvre",
        "description": "El Museo del Louvre es el museo nacional de Francia ...",
    }

    # B - We interrupt the Redis service and we make a new Idunn request
    # pylint: disable = protected-access
    docker_services._docker_compose.execute("stop", "wiki_redis")
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    # The wikipedia block should not be returned: we check we have all the
    # information, except the wikipedia block.
    resp = response.json()
    assert resp["id"] == "osm:relation:7515426"
    assert resp["name"] == "Museo del Louvre"
    assert resp["local_name"] == "Musée du Louvre"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert all(b["type"] != "wikipedia" for b in resp["blocks"][2].get("blocks"))

    # C - When Redis service restarts the wikipedia block should be returned again.
    restart_wiki_redis(docker_services)
    response = client.get(url="http://localhost/v1/pois/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    resp = response.json()

    assert resp["id"] == "osm:relation:7515426"
    assert resp["name"] == "Museo del Louvre"
    assert resp["local_name"] == "Musée du Louvre"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["blocks"][2].get("blocks")[0] == {
        "type": "wikipedia",
        "url": "https://es.wikipedia.org/wiki/Museo_del_Louvre",
        "title": "Museo del Louvre",
        "description": "El Museo del Louvre es el museo nacional de Francia ...",
    }
