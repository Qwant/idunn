import pytest
import responses
from app import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module", autouse=True)
def mock_wikipedia_response():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://fr.wikipedia.org/w/api.php",
            json={
                "query": {
                    "pages": [
                        {
                            "pageid": 69682,
                            "ns": 0,
                            "title": "Musée du Louvre",
                            "langlinks": [{"lang": "es", "title": "Museo del Louvre"}],
                        }
                    ]
                }
            },
        )

        rsps.add(
            responses.GET,
            "https://es.wikipedia.org/api/rest_v1/page/summary/Museo%20del%20Louvre",
            json={  # This is a subset of the real response
                "type": "standard",
                "title": "Museo del Louvre",
                "displaytitle": "Museo del Louvre",
                "content_urls": {
                    "desktop": {
                        "page": "https://es.wikipedia.org/wiki/Museo_del_Louvre",
                        "revisions": "https://es.wikipedia.org/wiki/Museo_del_Louvre?action=history",
                        "edit": "https://es.wikipedia.org/wiki/Museo_del_Louvre?action=edit",
                        "talk": "https://es.wikipedia.org/wiki/Discusión:Museo_del_Louvre",
                    },
                    "mobile": {
                        "page": "https://es.m.wikipedia.org/wiki/Museo_del_Louvre",
                        "revisions": "https://es.m.wikipedia.org/wiki/Special:History/Museo_del_Louvre",
                        "edit": "https://es.m.wikipedia.org/wiki/Museo_del_Louvre?action=edit",
                        "talk": "https://es.m.wikipedia.org/wiki/Discusión:Museo_del_Louvre",
                    },
                },
                "api_urls": {
                    "summary": "https://es.wikipedia.org/api/rest_v1/page/summary/Museo_del_Louvre",
                    "metadata": "https://es.wikipedia.org/api/rest_v1/page/metadata/Museo_del_Louvre",
                    "references": "https://es.wikipedia.org/api/rest_v1/page/references/Museo_del_Louvre",
                    "media": "https://es.wikipedia.org/api/rest_v1/page/media/Museo_del_Louvre",
                    "edit_html": "https://es.wikipedia.org/api/rest_v1/page/html/Museo_del_Louvre",
                    "talk_page_html": "https://es.wikipedia.org/api/rest_v1/page/html/Discusión:Museo_del_Louvre",
                },
                "extract": "El Museo del Louvre es el museo nacional de Francia ...",
                "extract_html": "<p>El <b>Museo del Louvre</b> es el museo nacional de Francia consagrado...</p>",
            },
        )
        yield


def test_wikipedia_another_language():
    """
    The louvre museum has the tag 'wikipedia' with value 'fr:Musée du Louvre'
    We check that wikipedia block is built using data from the wikipedia page
    in another language.
    """
    client = TestClient(app)
    response = client.get(url=f"http://localhost/v1/pois/osm:relation:7515426?lang=es",)

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
