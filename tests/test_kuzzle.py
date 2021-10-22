from fastapi.testclient import TestClient
import os
import re
import json
import responses
from .utils import enable_kuzzle

from app import app


@enable_kuzzle()
def test_kuzzle_event_ok():
    """
    Check the result of events contained in bbox
    """
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "kuzzle_event_response.json")
    with open(filepath, "r", encoding="utf-8") as f:
        json_event = json.load(f)

    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            "POST",
            re.compile(r"^http://localhost:7512/opendatasoft/events/"),
            status=200,
            json=json_event,
        )

        response = client.get(
            url="http://localhost/v1/events?bbox=2.0667651,48.432533,2.9384989,49.0349191& ,*&size=5",
        )

        assert len(rsps.calls) == 1

        resp = response.json()
        firstEventData = resp["events"][0]

        assert firstEventData["id"] == "event:openagenda_92106271"
        assert firstEventData["name"] == "Quand les livres expliquent la science"
        assert firstEventData["local_name"] == "Quand les livres expliquent la science"
        assert firstEventData["class_name"] == "event"
        assert firstEventData["subclass_name"] == "event"
        assert firstEventData["address"]["name"] == "Cité des Sciences et de l'Industrie"
        assert firstEventData["address"]["label"] == "30 Avenue Corentin Cariou, Paris"
        assert firstEventData["blocks"][0]["type"] == "event_opening_dates"
        assert firstEventData["blocks"][1]["type"] == "event_description"
        assert firstEventData["blocks"][2]["type"] == "website"
        assert firstEventData["blocks"][3]["type"] == "images"
        assert firstEventData["blocks"][0]["date_start"] == "2019-03-23T00:00:00Z"
        assert firstEventData["blocks"][3]["images"] == [
            {
                "url": "https://s2.qwant.com/thumbr/0x0/3/a/0639adb03540e9f45abb5a27668ac04d6f964aa30d99fa0275756d3d2b413b/evtbevent_conference-casse-croute-le-fonds-ancien-de-la-mediatheque-centre-ville_347092.jpg?u=http%3A%2F%2Fcibul.s3.amazonaws.com%2Fevtbevent_conference-casse-croute-le-fonds-ancien-de-la-mediatheque-centre-ville_347092.jpg&q=0&b=1&p=0&a=0",
                "alt": "Quand les livres expliquent la science",
                "credits": "",
                "source_url": "http://cibul.s3.amazonaws.com/evtbevent_conference-casse-croute-le-fonds-ancien-de-la-mediatheque-centre-ville_347092.jpg",
            },
            {
                "url": "https://s2.qwant.com/thumbr/0x0/7/f/c091d2d95f56f07beb1a2cd1c61f4d01a7ea4ab5079ab81b379baed315a48f/event_conference-casse-croute-le-fonds-ancien-de-la-mediatheque-centre-ville_347092.jpg?u=http%3A%2F%2Fcibul.s3.amazonaws.com%2Fevent_conference-casse-croute-le-fonds-ancien-de-la-mediatheque-centre-ville_347092.jpg&q=0&b=1&p=0&a=0",
                "alt": "Quand les livres expliquent la science",
                "credits": "",
                "source_url": "http://cibul.s3.amazonaws.com/event_conference-casse-croute-le-fonds-ancien-de-la-mediatheque-centre-ville_347092.jpg",
            },
        ]

        # We check that there is no Wikipedia block in the answer.
        assert all(b["type"] != "wikipedia" for b in firstEventData["blocks"])


def test_kuzzle_event_nok():
    """
    Check that an error  501 is raised when kuzzle port and address not set
    """
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "kuzzle_event_response.json")
    with open(filepath, "r", encoding="utf-8") as f:
        json_event = json.load(f)

    client = TestClient(app)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            "POST",
            re.compile(r"^http://localhost:7512/opendatasoft/events/"),
            status=200,
            json=json_event,
        )

        response = client.get(
            url="http://localhost/v1/events?bbox=2.0667651,48.432533,2.9384989,49.0349191& ,*&size=5",
        )

        assert response.status_code == 501
