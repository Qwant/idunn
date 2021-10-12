from idunn.places import PjApiPOI
from idunn.places.models import pj_info


def test_categories_pj():
    poi = PjApiPOI(pj_info.Response(**{"categories": []}))
    assert poi.get_class_name() is None
    assert poi.get_subclass_name() is None

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "restaurants"}]}))
    assert poi.get_class_name() == "restaurant"
    assert poi.get_subclass_name() == "restaurant"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "hôtels"}]}))
    assert poi.get_class_name() == "lodging"
    assert poi.get_subclass_name() == "lodging"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "salles de cinéma"}]}))
    assert poi.get_class_name() == "cinema"
    assert poi.get_subclass_name() == "cinema"

    poi = PjApiPOI(
        pj_info.Response(**{"categories": [{"category_name": "salles de concerts, de spectacles"}]})
    )
    assert poi.get_class_name() == "theatre"
    assert poi.get_subclass_name() == "theatre"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "Pharmacie"}]}))
    assert poi.get_class_name() == "pharmacy"
    assert poi.get_subclass_name() == "pharmacy"

    poi = PjApiPOI(
        pj_info.Response(**{"categories": [{"category_name": "supermarchés, hypermarchés"}]})
    )
    assert poi.get_class_name() == "supermarket"
    assert poi.get_subclass_name() == "supermarket"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "banques"}]}))
    assert poi.get_class_name() == "bank"
    assert poi.get_subclass_name() == "bank"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "cafés, bars"}]}))
    assert poi.get_class_name() == "bar"
    assert poi.get_subclass_name() == "bar"

    poi = PjApiPOI(
        pj_info.Response(**{"categories": [{"category_name": "des supers écoles de fou"}]})
    )
    assert poi.get_class_name() == "school"
    assert poi.get_subclass_name() == "school"

    poi = PjApiPOI(
        pj_info.Response(
            **{
                "categories": [
                    {"category_name": "grandes études"},
                    {"category_name": "ou bien l'enseignement supérieur"},
                ]
            }
        )
    )
    assert poi.get_class_name() == "college"
    assert poi.get_subclass_name() == "college"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": " Psychologue "}]}))
    assert poi.get_class_name() == "doctors"
    assert poi.get_subclass_name() == "doctors"

    poi = PjApiPOI(pj_info.Response(**{"categories": [{"category_name": "vétérinaires"}]}))
    assert poi.get_class_name() == "veterinary"
    assert poi.get_subclass_name() == "veterinary"

    poi = PjApiPOI(
        pj_info.Response(
            **{
                "categories": [
                    {"category_name": "unrelated category"},
                    {"category_name": "garages automobiles"},
                ]
            }
        )
    )
    assert poi.get_class_name() == "car"
    assert poi.get_subclass_name() == "car_repair"
