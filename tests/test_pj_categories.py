from idunn.places import LegacyPjPOI


def test_categories_pj():
    poi = LegacyPjPOI({"Category": ["None"]})
    assert poi.get_class_name() == None
    assert poi.get_subclass_name() == None

    poi = LegacyPjPOI({"Category": ["restaurants"]})
    assert poi.get_class_name() == "restaurant"
    assert poi.get_subclass_name() == "restaurant"

    poi = LegacyPjPOI({"Category": ["hôtels"]})
    assert poi.get_class_name() == "lodging"
    assert poi.get_subclass_name() == "lodging"

    poi = LegacyPjPOI({"Category": ["salles de cinéma"]})
    assert poi.get_class_name() == "cinema"
    assert poi.get_subclass_name() == "cinema"

    poi = LegacyPjPOI({"Category": ["salles de concerts, de spectacles"]})
    assert poi.get_class_name() == "theatre"
    assert poi.get_subclass_name() == "theatre"

    poi = LegacyPjPOI({"Category": ["Pharmacie"]})
    assert poi.get_class_name() == "pharmacy"
    assert poi.get_subclass_name() == "pharmacy"

    poi = LegacyPjPOI({"Category": ["supermarchés, hypermarchés"]})
    assert poi.get_class_name() == "grocery"
    assert poi.get_subclass_name() == "grocery"

    poi = LegacyPjPOI({"Category": ["banques"]})
    assert poi.get_class_name() == "bank"
    assert poi.get_subclass_name() == "bank"

    poi = LegacyPjPOI({"Category": ["cafés, bars"]})
    assert poi.get_class_name() == "bar"
    assert poi.get_subclass_name() == "bar"

    poi = LegacyPjPOI({"Category": ["des supers écoles de fou"]})
    assert poi.get_class_name() == "school"
    assert poi.get_subclass_name() == "school"

    poi = LegacyPjPOI({"Category": ["grandes études", "ou bien l'enseignement supérieur"]})
    assert poi.get_class_name() == "college"
    assert poi.get_subclass_name() == "college"

    poi = LegacyPjPOI({"Category": [" Psychologue "]})
    assert poi.get_class_name() == "doctors"
    assert poi.get_subclass_name() == "doctors"

    poi = LegacyPjPOI({"Category": ["vétérinaires"]})
    assert poi.get_class_name() == "veterinary"
    assert poi.get_subclass_name() == "veterinary"

    poi = LegacyPjPOI({"Category": ["unrelated category", "garages automobiles"]})
    assert poi.get_class_name() == "car"
    assert poi.get_subclass_name() == "car_repair"
