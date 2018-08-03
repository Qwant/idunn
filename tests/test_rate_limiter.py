import responses
import pytest
import re
from time import sleep
from freezegun import freeze_time
from app import app, settings
from apistar.test import TestClient
from idunn.blocks.wikipedia import WikipediaLimiter

from .test_api import louvre_museum


@pytest.fixture(scope="function")
def limiter_test_normal(redis):
    """
    We define here settings specific to tests.
    We define low max calls limits to avoid
    too large number of requests made
    """
    temp_period = settings._settings['WIKI_API_RL_PERIOD']
    temp_maxcalls = settings._settings['WIKI_API_RL_MAX_CALLS']

    settings._settings['WIKI_API_RL_PERIOD'] = 5
    # 2 wiki calls are made per request, so 6 max_calls mean 3 max wiki calls
    settings._settings['WIKI_API_RL_MAX_CALLS'] = 6
    settings._settings['WIKI_API_REDIS_URL'] = redis
    WikipediaLimiter._limiter = None
    yield
    settings._settings['WIKI_API_RL_PERIOD'] = temp_period
    settings._settings['WIKI_API_RL_MAX_CALLS'] = temp_maxcalls
    settings._settings['WIKI_API_REDIS_URL'] = None
    WikipediaLimiter._limiter = None

@pytest.fixture(scope="function")
def limiter_test_interruption(redis):
    """
    In the 'Redis interruption' test below
    we made more requests than the limits
    allowed by the fixture 'limiter_test_normal'
    So we need another specific fixture.
    """
    settings._settings['WIKI_API_REDIS_URL'] = redis
    WikipediaLimiter._limiter = None
    yield
    settings._settings['WIKI_API_REDIS_URL'] = None
    WikipediaLimiter._limiter = None

@pytest.fixture(scope='module', autouse=True)
def mock_wikipedia(redis):
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            'https://fr.wikipedia.org/w/api.php',
            json={
                "query": {
                    "pages": [{
                        "pageid": 69682,
                        "ns": 0,
                        "title": "Musée du Louvre",
                        "langlinks": [{"lang": "es", "title": "Museo del Louvre"}]
                    }]
                }
            }
        )

        rsps.add(
            responses.GET,
            'https://es.wikipedia.org/api/rest_v1/page/summary/Museo%20del%20Louvre',
            json={  # This is a subset of the real response
                "type": "standard",
                "title": "Museo del Louvre",
                "displaytitle": "Museo del Louvre",
                "content_urls": {
                    "desktop": {
                        "page": "https://es.wikipedia.org/wiki/Museo_del_Louvre",
                        "revisions": "https://es.wikipedia.org/wiki/Museo_del_Louvre?action=history",
                        "edit": "https://es.wikipedia.org/wiki/Museo_del_Louvre?action=edit",
                        "talk": "https://es.wikipedia.org/wiki/Discusión:Museo_del_Louvre"
                    },
                    "mobile": {
                        "page": "https://es.m.wikipedia.org/wiki/Museo_del_Louvre",
                        "revisions": "https://es.m.wikipedia.org/wiki/Special:History/Museo_del_Louvre",
                        "edit": "https://es.m.wikipedia.org/wiki/Museo_del_Louvre?action=edit",
                        "talk": "https://es.m.wikipedia.org/wiki/Discusión:Museo_del_Louvre"
                    },
                },
                "api_urls": {
                    "summary": "https://es.wikipedia.org/api/rest_v1/page/summary/Museo_del_Louvre",
                    "metadata": "https://es.wikipedia.org/api/rest_v1/page/metadata/Museo_del_Louvre",
                    "references": "https://es.wikipedia.org/api/rest_v1/page/references/Museo_del_Louvre",
                    "media": "https://es.wikipedia.org/api/rest_v1/page/media/Museo_del_Louvre",
                    "edit_html": "https://es.wikipedia.org/api/rest_v1/page/html/Museo_del_Louvre",
                    "talk_page_html": "https://es.wikipedia.org/api/rest_v1/page/html/Discusión:Museo_del_Louvre"
                },
                "extract": "El Museo del Louvre es el museo nacional de Francia ...",
                "extract_html": "<p>El <b>Museo del Louvre</b> es el museo nacional de Francia consagrado...</p>"
            }
        )
        yield rsps


def test_rate_limiter_with_redis(louvre_museum, limiter_test_normal, mock_wikipedia):
    """
    Test that Idunn stops external requests when
    we are above the max rate

    We mock 5 calls to wikipedia while the max number
    of calls is 3*2, so we test that after 3 calls
    no more calls are done
    """
    client = TestClient(app)

    for i in range(3):
        response = client.get(
           url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
        )
        resp = response.json()
        assert any(b['type'] == "wikipedia" for b in resp['blocks'][2].get('blocks'))

    for i in range(2):
        response = client.get(
            url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
        )
        resp = response.json()
        assert all(b['type'] != "wikipedia" for b in resp['blocks'][2].get('blocks'))

    assert len(mock_wikipedia.calls) == 6

def test_rate_limiter_without_redis(louvre_museum):
    """
    Test that Idunn doesn't stop external requests when
    no redis has been set: 10 requests to Idunn should
    generate 10 requests to Wikipedia API
    """
    client = TestClient(app)

    with responses.RequestsMock() as rsps:
        rsps.add('GET',
             re.compile('^https://.*\.wikipedia.org/'),
             status=200,
             json={"test": "test"}
        )
        for i in range(10):
            response = client.get(
               url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
            )

        assert len(rsps.calls) == 10


def restart_wiki_redis(docker_services):
    """
    Because docker services ports are
    dynamically chosen when the service starts
    we have to get the new port of the service.
    """
    docker_services.start('wiki_redis')
    """
    we have to remove the previous port of the
    redis service which has been stored in the dict '_services'
    before to get the new one
    """
    del docker_services._services['wiki_redis']
    port = docker_services.port_for("wiki_redis", 6379)
    url = f'{docker_services.docker_ip}:{port}'
    settings._settings['WIKI_API_REDIS_URL'] = url
    WikipediaLimiter._limiter = None

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_rate_limiter_with_redis_interruption(louvre_museum, docker_services, redis, limiter_test_interruption):
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

    response = client.get(
        url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
    )
    assert response.status_code == 200
    resp = response.json()

    """
    A/

    Before Redis interruption we check the answer is correct
    """
    assert resp['id'] == 'osm:relation:7515426'
    assert resp['name'] == "Museo del Louvre"
    assert resp['local_name'] == "Musée du Louvre"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['blocks'][2].get('blocks')[0] == {
        'type': 'wikipedia',
        'url': 'https://es.wikipedia.org/wiki/Museo_del_Louvre',
        'title': 'Museo del Louvre',
        'description': 'El Museo del Louvre es el museo nacional de Francia ...'
    }

    """
    B/

    We interrupt the Redis service and we make a new Idunn request
    """
    docker_services._docker_compose.execute('stop', 'wiki_redis')
    response = client.get(
        url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
    )
    assert response.status_code == 200
    """
    The wikipedia block should not be returned:
    we check we have all the information, except
    the wikipedia block.
    """
    resp = response.json()
    assert resp['id'] == 'osm:relation:7515426'
    assert resp['name'] == "Museo del Louvre"
    assert resp['local_name'] == "Musée du Louvre"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert all(b['type'] != "wikipedia" for b in resp['blocks'][2].get('blocks'))

    """
    C/

    When Redis service restarts the wikipedia block
    should be returned again.
    """
    restart_wiki_redis(docker_services)
    response = client.get(
        url=f'http://localhost/v1/pois/{louvre_museum}?lang=es',
    )
    assert response.status_code == 200
    resp = response.json()

    assert resp['id'] == 'osm:relation:7515426'
    assert resp['name'] == "Museo del Louvre"
    assert resp['local_name'] == "Musée du Louvre"
    assert resp['class_name'] == 'museum'
    assert resp['subclass_name'] == 'museum'
    assert resp['blocks'][2].get('blocks')[0] == {
        'type': 'wikipedia',
        'url': 'https://es.wikipedia.org/wiki/Museo_del_Louvre',
        'title': 'Museo del Louvre',
        'description': 'El Museo del Louvre es el museo nacional de Francia ...'
    }
