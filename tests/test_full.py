from apistar.test import TestClient
from freezegun import freeze_time
from app import app
import pytest
import json
from .test_api import load_poi

@pytest.fixture(scope="module")
def fake_all_blocks(mimir_client):
    """
    fill elasticsearch with a fake POI that contains all information possible
    in order that Idunn returns all possible blocks.
    """
    return load_poi('fake_all_blocks.json', mimir_client)

@freeze_time("2018-06-14 8:30:00", tz_offset=2)
def test_full(fake_all_blocks):
    """
    Exhaustive test that checks all possible blocks
    """
    client = TestClient(app)
    response = client.get(
        url=f'http://localhost/v1/pois/{fake_all_blocks}?lang=es',
    )

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
                        "type": "wikipedia",
                        "url": "https://es.wikipedia.org/wiki/Museo_de_Orsay",
                        "title": "Museo de Orsay",
                        "description": "El Museo de Orsay es una pinacoteca ubicada en París (Francia), que se dedica a las artes plásticas del siglo XIX y, más en concreto, del periodo 1848-1914. Ocupa el antiguo edificio de la estación ferroviaria de Orsay y alberga la mayor colección de obras impresionistas del mundo, con obras maestras de la pintura y de la escultura como Almuerzo sobre la hierba y Olympia de Édouard Manet, una prueba de la estatua La pequeña bailarina de catorce años de Degas, Baile en el Moulin de la Galette de Renoir, varias obras esenciales de Courbet e incluso cinco cuadros de la Serie des Catedrales de Rouen de Monet. Cronológicamente, este museo cubre la historia del arte entre los maestros antiguos y el arte moderno y contemporáneo."
                    },
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
