import responses
import pytest
import re
from app import app
from fastapi.testclient import TestClient
from freezegun import freeze_time
from idunn import settings
from idunn.datasources.wikipedia import WikipediaSession
from idunn.utils import rate_limiter
from idunn.utils.redis import RedisWrapper, get_redis_pool
from .test_api_with_wiki import mock_wikipedia_response
from .test_cache import has_wiki_desc
from .utils import override_settings

from redis import RedisError
from redis_rate_limit import RateLimiter
from functools import wraps


@pytest.fixture(scope="function")
def disable_redis():
    try:
        RedisWrapper.disable()
        yield
    finally:
        RedisWrapper.enable()


@pytest.fixture(scope="function")
def limiter_test_normal(redis, disable_redis):
    """
    We define here settings specific to tests.
    We define low max calls limits to avoid
    too large number of requests made
    """

    with override_settings(
        {"WIKI_API_RL_PERIOD": 5, "WIKI_API_RL_MAX_CALLS": 6, "REDIS_URL": redis}
    ):
        # To force settings overriding we need to set to None the limiter
        rate_limiter.redis_pool = get_redis_pool(settings["RATE_LIMITER_REDIS_DB"])
        WikipediaSession.Helpers._rate_limiter = None
        yield

    # We reset the rate limiter to remove the context of previous test
    rate_limiter.redis_pool = None
    WikipediaSession.Helpers._rate_limiter = None


@pytest.fixture(scope="function")
def limiter_test_interruption(redis, disable_redis):
    """
    In the 'Redis interruption' test below
    we made more requests than the limits
    allowed by the fixture 'limiter_test_normal'
    So we need another specific fixture.
    """
    with override_settings(
        {"WIKI_API_RL_PERIOD": 5, "WIKI_API_RL_MAX_CALLS": 100, "REDIS_URL": redis}
    ):
        rate_limiter.redis_pool = get_redis_pool(settings["RATE_LIMITER_REDIS_DB"])
        WikipediaSession.Helpers._rate_limiter = None
        yield

    rate_limiter.redis_pool = None
    WikipediaSession.Helpers._rate_limiter = None


def test_rate_limiter_with_redis(limiter_test_normal, mock_wikipedia_response):
    """
    Test that Idunn stops external requests when
    we are above the max rate

    Each call to Idunn (with cache disabled) outputs a block with Wikipedia
    data, which requires 2 requests to build (to translate the title and then to
    fetch actual content).

    As `WIKI_API_RL_MAX_CALLS` is set to 6, the blocks won't be displayed
    after the 3rd request.
    """
    client = TestClient(app)

    for _ in range(3):
        response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")
        resp = response.json()
        assert has_wiki_desc(resp)

    for _ in range(2):
        response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")
        resp = response.json()
        assert not has_wiki_desc(resp)

    assert len(mock_wikipedia_response.calls) == 6


def test_rate_limiter_without_redis(disable_redis):
    """
    Test that Idunn doesn't stop external requests when
    no redis has been set: 10 requests to Idunn should
    generate 20 requests to Wikipedia API
    """
    client = TestClient(app)

    with responses.RequestsMock() as rsps:
        rsps.add(
            "GET", re.compile(r"^https://.*\.wikipedia.org/"), status=200, json={"test": "test"}
        )
        for _ in range(10):
            client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")

        assert len(rsps.calls) == 10


def restart_wiki_redis(docker_services):
    """
    Because docker services ports are
    dynamically chosen when the service starts
    we have to get the new port of the service.
    """
    docker_services.start("wiki_redis")
    # We have to remove the previous port of the redis service which has been
    # stored in the dict '_services' before to get the new one.
    del docker_services._services["wiki_redis"]
    port = docker_services.port_for("wiki_redis", 6379)
    url = f"{docker_services.docker_ip}:{port}"
    settings._settings["REDIS_URL"] = url
    rate_limiter.redis_pool = get_redis_pool(settings["RATE_LIMITER_REDIS_DB"])
    WikipediaSession.Helpers._rate_limiter = None


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
    response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")

    assert response.status_code == 200
    resp = response.json()
    # Here the redis is on so the answer should contain the wikipedia block.
    assert has_wiki_desc(resp)

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
        response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")

        assert response.status_code == 200
        resp = response.json()
        # No wikipedia block should be in the answer.
        assert not has_wiki_desc(resp)

    # Now that the redis "came back", we are expecting a correct answer from
    # Idunn.
    response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")

    assert response.status_code == 200
    resp = response.json()
    # Here the redis is on so the answer should contain the wikipedia block
    assert has_wiki_desc(resp)


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

    response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    resp = response.json()

    # A - Before Redis interruption we check the answer is correct
    assert resp["id"] == "osm:relation:7515426"
    assert resp["name"] == "Museo del Louvre"
    assert resp["local_name"] == "Musée du Louvre"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["blocks"][4] == {
        "type": "description",
        "description": "El Museo del Louvre es el museo nacional de Francia ...",
        "source": "wikipedia",
        "url": "https://es.wikipedia.org/wiki/Museo_del_Louvre",
    }

    # B - We interrupt the Redis service and we make a new Idunn request
    docker_services._docker_compose.execute("stop", "wiki_redis")
    response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    # The wikipedia block should not be returned: we check we have all the
    # information, except the wikipedia block.
    resp = response.json()
    assert resp["id"] == "osm:relation:7515426"
    assert resp["name"] == "Museo del Louvre"
    assert resp["local_name"] == "Musée du Louvre"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert not has_wiki_desc(resp)

    # C - When Redis service restarts the wikipedia block should be returned again.
    restart_wiki_redis(docker_services)
    response = client.get(url="http://localhost/v1/places/osm:relation:7515426?lang=es")
    assert response.status_code == 200
    resp = response.json()

    assert resp["id"] == "osm:relation:7515426"
    assert resp["name"] == "Museo del Louvre"
    assert resp["local_name"] == "Musée du Louvre"
    assert resp["class_name"] == "museum"
    assert resp["subclass_name"] == "museum"
    assert resp["blocks"][4] == {
        "type": "description",
        "description": "El Museo del Louvre es el museo nacional de Francia ...",
        "source": "wikipedia",
        "url": "https://es.wikipedia.org/wiki/Museo_del_Louvre",
    }
