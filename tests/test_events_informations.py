from freezegun import freeze_time
from unittest.mock import ANY
from idunn.blocks.events import DescriptionEvent, OpeningDayEvent
from idunn.places import POI

"""
In this module we test that the opening_hours block for
a POI located in a different timezone (Moscow) contains
the correct information.

For each test we freeze time at different datetimes and
for each we create a fake different OpeningHourBlock from
a raw json extracted from a POI located in Moscow city.

TODO: a test that checks that opening hours can now span
over midnight (branch 'new-parsing' of the repo)
"""


def get_event_information_complete_fields():
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return DescriptionEvent.from_es(
        POI({
            "type": "event_description",
            "description": "15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
            "free_text": "Lectures d'albums pour les plus petits (3-6 ans). À partir de 15h. Accès libre et gratuit \n\n**Batiment**: Niveau 0-Bibliothèque jeunesse \n\n**Thèmes**: Sciences et société \n\n**Activités**: Animation",
            "price": "Gratuit"
        }),
        lang='en'
    )


def get_event_information_missing_fields():
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return DescriptionEvent.from_es(
        POI({
            "type": "event_description",
            "description": "15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
            "price": "Gratuit"
        }),
        lang='en'
    )


def get_event_information_no_fields():
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return DescriptionEvent.from_es(
        POI({
        }),
        lang='en'
    )


def test_event_information_complete():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    ode_block = get_event_information_complete_fields()

    assert ode_block == DescriptionEvent(
        type="event_description",
        description="15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
        free_text="Lectures d'albums pour les plus petits (3-6 ans). À partir de 15h. Accès libre et gratuit \n\n**Batiment**: Niveau 0-Bibliothèque jeunesse \n\n**Thèmes**: Sciences et société \n\n**Activités**: Animation",
        price="Gratuit"
    )


def test_event_information_missing_fields():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    ode_block = get_event_information_missing_fields()
    print(ode_block)
    assert ode_block == DescriptionEvent(
        type="event_description",
        description="15h-16h [LECTURES D'ALBUMS] Pour les petits (3-6 ans). Accès libre et gratuit.",
        free_text=None,
        price="Gratuit"
    )


def test_event_information_no_fields():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    ode_block = get_event_information_no_fields()

    assert ode_block is None
