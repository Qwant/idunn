from idunn.places import PjPOI

def test_categories_pj():
    poi = PjPOI({'Category': ['None']})
    assert poi.get_class_name() == None
    assert poi.get_subclass_name() == None

    poi = PjPOI({'Category': ['restaurants']})
    assert poi.get_class_name() == 'restaurant'
    assert poi.get_subclass_name() == 'restaurant'

    poi = PjPOI({'Category': ['hôtels']})
    assert poi.get_class_name() == 'lodging'
    assert poi.get_subclass_name() == 'lodging'

    poi = PjPOI({'Category': ['salles de cinéma']})
    assert poi.get_class_name() == 'cinema'
    assert poi.get_subclass_name() == 'cinema'

    poi = PjPOI({'Category': ['salles de concerts, de spectacles']})
    assert poi.get_class_name() == 'theatre'
    assert poi.get_subclass_name() == 'theatre'

    poi = PjPOI({'Category': ['Pharmacie']})
    assert poi.get_class_name() == 'pharmacy'
    assert poi.get_subclass_name() == 'pharmacy'

    poi = PjPOI({'Category': ['supermarchés, hypermarchés']})
    assert poi.get_class_name() == 'grocery'
    assert poi.get_subclass_name() == 'grocery'

    poi = PjPOI({'Category': ['banques']})
    assert poi.get_class_name() == 'bank'
    assert poi.get_subclass_name() == 'bank'

    poi = PjPOI({'Category': ['cafés, bars']})
    assert poi.get_class_name() == 'bar'
    assert poi.get_subclass_name() == 'bar'

    poi = PjPOI({'Category': ['des supers écoles de fou']})
    assert poi.get_class_name() == 'school'
    assert poi.get_subclass_name() == 'school'

    poi = PjPOI({'Category': ['grandes études', 'ou bien l\'enseignement supérieur']})
    assert poi.get_class_name() == 'college'
    assert poi.get_subclass_name() == 'college'

    poi = PjPOI({'Category': [' Psychologue ']})
    assert poi.get_class_name() == 'health'
    assert poi.get_subclass_name() == 'health'

    poi = PjPOI({'Category': ['vétérinaires ']})
    assert poi.get_class_name() == 'health'
    assert poi.get_subclass_name() == 'health'

    poi = PjPOI({'Category': [' police']})
    assert poi.get_class_name() == 'service'
    assert poi.get_subclass_name() == 'service'

    poi = PjPOI({'Category': [' centres de secours']})
    assert poi.get_class_name() == 'service'
    assert poi.get_subclass_name() == 'service'

    poi = PjPOI({'Category': ['agences immobilière']})
    assert poi.get_class_name() == 'building'
    assert poi.get_subclass_name() == 'building'
