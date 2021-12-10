from app import app
from fastapi.testclient import TestClient
from idunn.blocks.services_and_information import AccessibilityBlock
from idunn.places import POI


def test_accessibility_block():
    accessibility_block = AccessibilityBlock.from_es(
        POI(
            {
                "properties": {"wheelchair": "limited", "toilets:wheelchair": "no"},
                "id": "osm:way:154422021",
            }
        ),
        lang="en",
    )

    assert accessibility_block == AccessibilityBlock(wheelchair="partial", toilets_wheelchair="no")


def test_accessibility_unknown():
    accessibility_block = AccessibilityBlock.from_es(
        POI(
            {
                "properties": {
                    "wheelchair": "toto",
                },
                "id": "osm:way:154422021",
            }
        ),
        lang="en",
    )
    assert accessibility_block is None


def test_undefined_wheelchairs():
    """
    Test that when wheelchair and toilets_wheelchair are not
    defined there is no block 'accessibility'
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:node:738042332?lang=fr")

    assert response.status_code == 200

    resp = response.json()

    assert resp["id"] == "osm:node:738042332"
    assert resp["name"] == "Boulangerie Patisserie Peron"
    assert resp["local_name"] == "Boulangerie Patisserie Peron"
    assert resp["class_name"] == "bakery"
    assert resp["subclass_name"] == "bakery"
    assert resp["blocks"] == []


def test_wheelchair():
    """
    Test that Idunn returns the correct block when
    both wheelchair and toilets_wheelchair tags
    are defined
    """
    client = TestClient(app)
    response = client.get(url="http://localhost/v1/places/osm:node:36153811?lang=fr")

    assert response.status_code == 200

    resp = response.json()

    assert resp["id"] == "osm:node:36153811"
    assert resp["name"] == "Multiplexe Liberté"
    assert resp["local_name"] == "Multiplexe Liberté"
    assert resp["class_name"] == "cinema"
    assert resp["subclass_name"] == "cinema"
    assert resp["blocks"] == [
        {
            "blocks": [
                {
                    "blocks": [
                        {"toilets_wheelchair": "yes", "type": "accessibility", "wheelchair": "yes"}
                    ],
                    "type": "services_and_information",
                }
            ],
            "type": "information",
        }
    ]
