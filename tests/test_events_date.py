from freezegun import freeze_time
from unittest.mock import ANY
from idunn.blocks.events import DescriptionEvent, OpeningDayEvent
from idunn.places import POI

"""
In this module we test the events return. check if fields
are correctly returned

"""

def get_event_day_complete_fields():
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return OpeningDayEvent.from_es(
        POI({
            "date_start": "2019-03-23T00:00:00.000Z",
            "date_end": "2019-05-25T00:00:00.000Z",
            "space_time_info":  "du samedi 23 mars au samedi 25 mai à Cité des Sciences et de l'Industrie",
            "timetable":  "2019-03-23T15:00:00 2019-03-23T16:00:00;2019-04-13T15:00:00 2019-04-13T16:00:00;2019-05-25T15:00:00 2019-05-25T16:00:00"
        }),
        lang='en'
    )


def get_event_day_missing_fields():
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return OpeningDayEvent.from_es(
        POI({
            "date_start": "2019-03-23T00:00:00.000Z",
            "date_end": "2019-05-25T00:00:00.000Z",
        }),
        lang='en'
    )


def get_event_day_no_fields():
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return OpeningDayEvent.from_es(
        POI({
        }),
        lang='en'
    )


def test_event_day_complete():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    ode_block = get_event_day_complete_fields()

    assert ode_block == OpeningDayEvent(
        type="event_opening_date",
        date_start="2019-03-23T00:00:00.000Z",
        date_end="2019-05-25T00:00:00.000Z",
        space_time_info="du samedi 23 mars au samedi 25 mai à Cité des Sciences et de l'Industrie",
        timetable=[
            "2019-03-23T15:00:00 2019-03-23T16:00:00",
            "2019-04-13T15:00:00 2019-04-13T16:00:00",
            "2019-05-25T15:00:00 2019-05-25T16:00:00"
        ]
    )


def test_event_day_missing_fields():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    ode_block = get_event_day_missing_fields()
    print(ode_block)
    assert ode_block == OpeningDayEvent(
        type="event_opening_date",
        date_start="2019-03-23T00:00:00.000Z",
        date_end="2019-05-25T00:00:00.000Z",
        space_time_info=None,
        timetable=None
    )


def test_event_day_no_fields():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    ode_block = get_event_day_no_fields()

    assert ode_block is None
