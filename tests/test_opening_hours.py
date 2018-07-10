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
    We freeze time at 8h30 UTC (ie. 11h30 Moscow)
    The POI located in Moscow should be open since
    it opens at 10h00 every day and the local time
    is 11h30.
    """
    oh_block = get_moscow_poi("Mo-Su 10:00-22:00")

    assert oh_block == OpeningHourBlock(
        type='opening_hours',
        status='open',
        next_transition_datetime='2018-06-14T22:00:00+03:00',
        seconds_before_next_transition=37800,
        is_24_7=False,
        raw='Mo-Su 10:00-22:00',
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
                "opening_hours": [{"beginning": "10:00", "end": "22:00"}]
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


@freeze_time("2018-06-15T21:00:00+03:00")
def test_opening_hour_days_cycle():
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
