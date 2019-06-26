from freezegun import freeze_time
from unittest.mock import ANY
from idunn.blocks.events import DescriptionEvent, OpeningDayEvent
from idunn.places import POI

"""
In this module we test the events block OpeningDayEvent. check if fields
are correctly returned

"""

def get_event_day_complete_fields():
    """
    returns an OpeningDayEvent with all features and multiple timetables
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

def get_event_day_complete_fields_with_one_timetable():
    """
    returns an OpeningDayEvent with all features and simple timetable
    """
    return OpeningDayEvent.from_es(
        POI({
            "date_start": "2019-03-23T00:00:00.000Z",
            "date_end": "2019-05-25T00:00:00.000Z",
            "space_time_info":  "du samedi 23 mars au samedi 25 mai à Cité des Sciences et de l'Industrie",
            "timetable":  "2019-03-23T15:00:00 2019-03-23T16:00:00"
        }),
        lang='en'
    )



def get_event_day_missing_fields():
    """
    returns an OpeningDayEvent with date start and date end
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
    returns an OpeningDayEvent empty
    """
    return OpeningDayEvent.from_es(
        POI({
        }),
        lang='en'
    )


def test_event_day_complete():
    """
    test OpeningDayEvent withall the features and timetable with different scheduled
    """
    ode_block = get_event_day_complete_fields()

    assert ode_block == OpeningDayEvent(
        type="event_opening_date",
        date_start="2019-03-23T00:00:00.000Z",
        date_end="2019-05-25T00:00:00.000Z",
        space_time_info="du samedi 23 mars au samedi 25 mai à Cité des Sciences et de l'Industrie",
        timetable=[
            {"begin": "2019-03-23T15:00:00", "end": "2019-03-23T16:00:00"},
            {"begin": "2019-04-13T15:00:00", "end": "2019-04-13T16:00:00"},
            {"begin": "2019-05-25T15:00:00", "end": "2019-05-25T16:00:00"},
        ]
    )

def test_event_day_complete_with_one_timetable():
    """
    test OpeningDayEvent wit hall the features and simple timetable
    """
    ode_block = get_event_day_complete_fields_with_one_timetable()

    assert ode_block == OpeningDayEvent(
        type="event_opening_date",
        date_start="2019-03-23T00:00:00.000Z",
        date_end="2019-05-25T00:00:00.000Z",
        space_time_info="du samedi 23 mars au samedi 25 mai à Cité des Sciences et de l'Industrie",
        timetable=[
            {"begin": "2019-03-23T15:00:00", "end": "2019-03-23T16:00:00"}
        ]
    )


def test_event_day_missing_fields():
    """
    test OpeningDayEvent with ano space_time_info and no timetable
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
    test OpeningDayEvent with no features
    """
    ode_block = get_event_day_no_fields()

    assert ode_block is None
