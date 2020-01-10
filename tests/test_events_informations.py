from idunn.blocks.events import DescriptionEvent
from idunn.places import Event

"""
    In this module we test the events block DescriptionEvent. check if fields
    are correctly returned

"""


def get_event_information_complete_fields():
    """
    returns an DescriptionEvent with all features (type, description, free_text, pricing_info)
    """
    return DescriptionEvent.from_es(
        Event(
            {
                "type": "event_description",
                "description": "15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
                "free_text": "Lectures d'albums pour les plus petits (3-6 ans). À partir de 15h. Accès libre et gratuit \n\n**Batiment**: Niveau 0-Bibliothèque jeunesse \n\n**Thèmes**: Sciences et société \n\n**Activités**: Animation",
                "pricing_info": "Gratuit",
                "tags": "concert;jazz",
            }
        ),
        lang="en",
    )


def get_event_information_missing_fields():
    """
    returns an DescriptionEvent with feature free_text missing
    """
    return DescriptionEvent.from_es(
        Event(
            {
                "type": "event_description",
                "description": "15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
                "pricing_info": "Gratuit",
            }
        ),
        lang="en",
    )


def get_event_information_no_fields():
    """
    returns an DescriptionEvent with no features
    """
    return DescriptionEvent.from_es(Event({}), lang="en")


def test_event_information_complete():
    """
    test DescriptionEvent block ok with all features (type, description, free_text, pricing_info)
    """
    ode_block = get_event_information_complete_fields()

    assert ode_block == DescriptionEvent(
        type="event_description",
        description="15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
        free_text="Lectures d'albums pour les plus petits (3-6 ans). À partir de 15h. Accès libre et gratuit \n\n**Batiment**: Niveau 0-Bibliothèque jeunesse \n\n**Thèmes**: Sciences et société \n\n**Activités**: Animation",
        price="Gratuit",
        tags=["concert", "jazz"],
    )


def test_event_information_missing_fields():
    """
    test DescriptionEvent block ok with feature free_text missing
    """
    ode_block = get_event_information_missing_fields()

    assert ode_block == DescriptionEvent(
        type="event_description",
        description="15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
        free_text=None,
        price="Gratuit",
        tags=[],
    )


def test_event_information_no_fields():
    """
    test DescriptionEvent block ok with no feature
    """
    ode_block = get_event_information_no_fields()

    assert ode_block is None
