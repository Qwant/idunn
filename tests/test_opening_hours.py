import pytest
from freezegun import freeze_time
from unittest.mock import ANY
from idunn.blocks.opening_hour import OpeningHourBlock

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

def get_moscow_poi(opening_hours):
    """
    returns an OpeningHourBlock from a fake json
    corresponding to a POI located in moscow city
    for different opening_hours formats.
    """
    return OpeningHourBlock.from_es(
        {
            "coord": {
                "lon": 37.588161523500276,
                "lat": 55.74831406552745
            },
            "properties": {
                "opening_hours": opening_hours
            }
        },
        lang='en'
    )

@freeze_time("2018-06-14 8:30:00", tz_offset=0)
def test_opening_hour_open():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    oh_block = get_moscow_poi("Mo-Sa 10:00-22:00; Su 10:00-14:00, 18:00-22:00")

    assert oh_block == OpeningHourBlock(
        type='opening_hours',
        status='open',
        next_transition_datetime='2018-06-14T22:00:00+03:00',
        seconds_before_next_transition=37800,
        is_24_7=False,
        raw='Mo-Sa 10:00-22:00; Su 10:00-14:00,18:00-22:00',
        days=[
            {
                "dayofweek": 1,
                "local_date": "2018-06-11",
                "status": "open",
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
            },
            {
                "dayofweek": 2,
                "local_date": "2018-06-12",
                "status": "open",
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
            },
            {
                "dayofweek": 3,
                "local_date": "2018-06-13",
                "status": "open",
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
            },
            {
                "dayofweek": 4,
                "local_date": "2018-06-14",
                "status": "open",
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
            },
            {
                "dayofweek": 5,
                "local_date": "2018-06-15",
                "status": "open",
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
            },
            {
                "dayofweek": 6,
                "local_date": "2018-06-16",
                "status": "open",
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
            },
            {
                "dayofweek": 7,
                "local_date": "2018-06-17",
                "status": "open",
                "opening_hours": [
                    {"beginning": "10:00", "end": "14:00"},
                    {"beginning": "18:00", "end": "22:00"},
                ]
            },
        ]
    )

@freeze_time("2018-06-14 21:30:00", tz_offset=0)
def test_opening_hour_close():
    """
    The POI should already be closed since it's 21h30 UTC while
    the POI closes at 22h00 in UTC+3.
    """
    oh_block = get_moscow_poi("Mo-Su 10:00-22:00")

    assert oh_block.status == 'closed'
    assert oh_block.next_transition_datetime == '2018-06-15T10:00:00+03:00'
    assert oh_block.seconds_before_next_transition == 34200
    assert oh_block.is_24_7 ==  False
    assert oh_block.raw == 'Mo-Su 10:00-22:00'
    assert len(oh_block.days) == 7
    assert all(d.status == 'open' for d in oh_block.days)


@freeze_time("2018-06-14 21:30:00", tz_offset=0)
def test_opening_hour_next_year():
    """
    The POI is open only in Jan and Feb, and we are in Jun.
    So it's closed, and it will be open the 2019/01/01.
    """
    oh_block = get_moscow_poi("Jan-Feb 10:00-20:00")

    assert dict(oh_block) == dict(
        type='opening_hours',
        status='closed',
        next_transition_datetime='2019-01-01T10:00:00+03:00',
        seconds_before_next_transition=17314200,
        is_24_7=False,
        raw='Jan-Feb 10:00-20:00',
        days=ANY
    )
    assert len(oh_block.days) == 7
    assert all(d.status == 'closed' for d in oh_block.days)


@freeze_time("2018-06-14T23:00:00+03:00")
def test_opening_hour_open_until_midnight():
    oh_block = get_moscow_poi("Mo-Su 09:00-00:00")
    assert oh_block == dict(
        type='opening_hours',
        status='open',
        next_transition_datetime='2018-06-15T00:00:00+03:00',
        seconds_before_next_transition=3600,
        is_24_7=False,
        raw='Mo-Su 09:00-24:00',
        days=ANY
    )
    assert len(oh_block.days) == 7
    assert all(d.status == 'open' for d in oh_block.days)
    assert all(d.opening_hours == [dict(
        beginning='09:00',
        end='00:00'
    )] for d in oh_block.days)

@freeze_time("2018-01-04T23:00:00+03:00")
def test_opening_hour_open_until_2am():
    oh_block = get_moscow_poi("Mo-Su 09:00-02:00")
    assert oh_block == dict(
        type='opening_hours',
        status='open',
        next_transition_datetime='2018-01-05T02:00:00+03:00',
        seconds_before_next_transition=10800,
        is_24_7=False,
        raw='Mo-Su 09:00-02:00',
        days=ANY
    )
    assert len(oh_block.days) == 7
    assert all(d.status == 'open' for d in oh_block.days)
    assert all(d.opening_hours == [dict(
        beginning='09:00',
        end='02:00'
    )] for d in oh_block.days)

@freeze_time("2018-10-26T15:00:00+03:00")
def test_opening_hour_close_until_19pm():
    oh_block = get_moscow_poi("Mo-Su 12:00-14:30; Mo-Su,PH 19:00-22:30")
    assert oh_block == dict(
        type='opening_hours',
        status='closed',
        next_transition_datetime='2018-10-26T19:00:00+03:00',
        seconds_before_next_transition=14400,
        is_24_7=False,
        raw='Mo-Su 12:00-14:30; Mo-Su,PH 19:00-22:30',
        days=ANY
    )
    assert len(oh_block.days) == 7
    assert all(d.status == 'open' for d in oh_block.days)

@freeze_time("2018-06-15T21:00:00+03:00")
def test_opening_hour_days_cycle():
    """
    Opening_hours values where a day range ends with Monday,
    to test if the "cycle" is parsed correctly.
    """
    oh_block = get_moscow_poi("We-Mo 11:00-19:00")
    assert oh_block == dict(
        type='opening_hours',
        status='closed',
        next_transition_datetime='2018-06-16T11:00:00+03:00',
        seconds_before_next_transition=50400,
        is_24_7=False,
        raw='We-Mo 11:00-19:00',
        days=[
            {
                "dayofweek": 1,
                "local_date": "2018-06-11",
                "status": "open",
                "opening_hours": [{"beginning": "11:00", "end": "19:00"}]
            },
            {
                "dayofweek": 2,
                "local_date": "2018-06-12",
                "status": "closed",
                "opening_hours": []
            },
            {
                "dayofweek": 3,
                "local_date": "2018-06-13",
                "status": "open",
                "opening_hours": [{"beginning": "11:00", "end": "19:00"}]
            },
            {
                "dayofweek": 4,
                "local_date": "2018-06-14",
                "status": "open",
                "opening_hours": [{"beginning": "11:00", "end": "19:00"}]
            },
            {
                "dayofweek": 5,
                "local_date": "2018-06-15",
                "status": "open",
                "opening_hours": [{"beginning": "11:00", "end": "19:00"}]
            },
            {
                "dayofweek": 6,
                "local_date": "2018-06-16",
                "status": "open",
                "opening_hours": [{"beginning": "11:00", "end": "19:00"}]
            },
            {
                "dayofweek": 7,
                "local_date": "2018-06-17",
                "status": "open",
                "opening_hours": [{"beginning": "11:00", "end": "19:00"}]
            },
        ]
    )

@freeze_time("2018-06-30T11:00:00+03:00")
def test_opening_hour_sunrise_sunset():
    """
    Opening_hours sunrise-sunset.
    """
    oh_block = get_moscow_poi("sunrise-sunset")

    assert dict(oh_block) == dict(
        type='opening_hours',
        status='open',
        next_transition_datetime="2018-06-30T21:18:00+03:00",
        seconds_before_next_transition=37080,
        is_24_7=False,
        raw='sunrise-sunset',
        days=[
            {
                "dayofweek": 1,
                "local_date": "2018-06-25",
                "status": "open",
                "opening_hours": [{"beginning": "03:46", "end": "21:18"}]
            },
            {
                "dayofweek": 2,
                "local_date": "2018-06-26",
                "status": "open",
                "opening_hours": [{"beginning": "03:46", "end": "21:18"}]
            },
            {
                "dayofweek": 3,
                "local_date": "2018-06-27",
                "status": "open",
                "opening_hours": [{"beginning": "03:47", "end": "21:18"}]
            },
            {
                "dayofweek": 4,
                "local_date": "2018-06-28",
                "status": "open",
                "opening_hours": [{"beginning": "03:48", "end": "21:18"}]
            },
            {
                "dayofweek": 5,
                "local_date": "2018-06-29",
                "status": "open",
                "opening_hours": [{"beginning": "03:48", "end": "21:18"}]
            },
            {
                "dayofweek": 6,
                "local_date": "2018-06-30",
                "status": "open",
                "opening_hours": [{"beginning": "03:49", "end": "21:18"}]
            },
            {
                "dayofweek": 7,
                "local_date": "2018-07-01",
                "status": "open",
                "opening_hours": [{"beginning": "03:50", "end": "21:17"}]
            },
        ]
    )

@freeze_time("2018-06-30T11:00:00+03:00")
def test_opening_hour_24_7():
    """
    Opening_hours 24/7.
    """
    oh_block = get_moscow_poi("24/7")
    assert oh_block == dict(
        type='opening_hours',
        status='open',
        next_transition_datetime=None,
        seconds_before_next_transition=None,
        is_24_7=True,
        raw='24/7',
        days=[
            {
                "dayofweek": 1,
                "local_date": "2018-06-25",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
            {
                "dayofweek": 2,
                "local_date": "2018-06-26",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
            {
                "dayofweek": 3,
                "local_date": "2018-06-27",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
            {
                "dayofweek": 4,
                "local_date": "2018-06-28",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
            {
                "dayofweek": 5,
                "local_date": "2018-06-29",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
            {
                "dayofweek": 6,
                "local_date": "2018-06-30",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
            {
                "dayofweek": 7,
                "local_date": "2018-07-01",
                "status": "open",
                "opening_hours": [{"beginning": "00:00", "end": "00:00"}]
            },
        ]
    )

@freeze_time("2019-02-10T11:00:00+03:00")
@pytest.mark.skip(reason="fail until hoh issue 26 is fixed")
def test_opening_hour_2_years():
    """
    Opening_hours span over 2 years without explicit years.
    """
    oh_block = get_moscow_poi("Oct-Mar 07:30-19:30; Apr-Sep 07:00-21:00")
    assert oh_block == dict(
        type='opening_hours',
        status='open',
        next_transition_datetime='2019-02-10T19:30:00+03:00',
        seconds_before_next_transition=30600,
        is_24_7=True,
        raw='Oct-Mar 07:30-19:30; Apr-Sep 07:00-21:00',
        days=ANY
    )
