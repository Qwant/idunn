import responses
import pytest
import re
from freezegun import freeze_time
from app import app
from apistar.test import TestClient
from idunn.blocks.wikipedia import wiki_breaker

from .test_full import fake_all_blocks

@pytest.fixture(scope="module", autouse=False)
def mock_wiki_requests():
    with responses.RequestsMock() as rsps:
        rsps.add('GET',
                 re.compile('^https://.*\.wikipedia.org/'),
                 status=500)
        yield rsps

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_circuit_breaker(fake_all_blocks, mock_wiki_requests):
    """
    Test that all possible blocks are correct even
    if the circuit is open.
    We mock 20 calls to wikipedia while the max number
    of failure is 15, so we test that after 15 calls
    the circuit is open (ie there are no more than 15
    calls).
    """

    client = TestClient(app)
    wiki_breaker.close()
    for i in range(20):
        response = client.get(
            url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
        )
    assert wiki_breaker.fail_counter == len(mock_wiki_requests.calls)

    assert response.status_code == 200
    resp = response.json()

    assert resp == {
        "id": "osm:way:7777777",
        "name": "Fako Allo",
        "local_name": "Fake All",
        "class_name": "museum",
        "subclass_name": "museum",
        "geometry": {
            "coordinates": [
                2.3250037768187326,
                48.86618482685007
            ],
            "type": "Point"
        },
        "address": {
            "label": "62B Rue de Lille (Paris)"
        },
        "blocks": [
            {
                "type": "opening_hours",
                "status": "open",
                "next_transition_datetime": "2018-06-14T18:00:00+02:00",
                "seconds_before_next_transition": 27000,
                "is_24_7": False,
                "raw": "Tu-Su 09:30-18:00; Th 09:30-21:45",
                "days": []
            },
            {
                "type": "phone",
                "url": "tel:+33140494814",
                "international_format": "+33140494814",
                "local_format": "+33140494814"
            },
            {
                "type": "information",
                "blocks": [
                    {
                        "type": "services_and_information",
                        "blocks": [
                            {
                                "type": "accessibility",
                                "wheelchair": "true",
                                "tactile_paving": "false",
                                "toilets_wheelchair": "false"
                            },
                            {
                                "type": "internet_access",
                                "wifi": True
                            },
                            {
                                "type": "brewery",
                                "beers": [
                                    {
                                        "name": "Kilkenny"
                                    },
                                    {
                                        "name": "Guinness"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "type": "website",
                "url": "http://testing.test"
            },
            {
                "type": "contact",
                "url": "mailto:contact@example.com",
            },
        ]
    }
