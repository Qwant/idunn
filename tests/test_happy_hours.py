from freezegun import freeze_time
from unittest.mock import ANY
from idunn.blocks.opening_hour import HappyHourBlock
from idunn.places import POI

"""
Most of this code comes from test_opening_hours.py
"""


def get_moscow_poi(happy_hours):
    return HappyHourBlock.from_es(
        POI(
            {
                "coord": {"lon": 37.588161523500276, "lat": 55.74831406552745},
                "properties": {"happy_hours": happy_hours},
            }
        ),
        lang="en",
    )


@freeze_time("2018-06-14 18:30:00", tz_offset=0)
def test_happy_hour():
    """
    We freeze time at 8:30 UTC (ie. 11:30 in Moscow)
    The POI located in Moscow should be open since
    it opens at 10:00 every day and the local time
    is 11:30.
    """
    hh_block = get_moscow_poi("Mo-Sa 20:00-22:00; Su 12:00-14:00, 20:00-22:00")

    assert hh_block == HappyHourBlock(
        type="happy_hours",
        status="open",
        next_transition_datetime="2018-06-14T22:00:00+03:00",
        seconds_before_next_transition=1800,
        is_24_7=False,
        raw="Mo-Sa 20:00-22:00; Su 12:00-14:00, 20:00-22:00",
        days=[
            {
                "dayofweek": 1,
                "local_date": "2018-06-11",
                "status": "open",
                "opening_hours": [{"beginning": "20:00", "end": "22:00"}],
            },
            {
                "dayofweek": 2,
                "local_date": "2018-06-12",
                "status": "open",
                "opening_hours": [{"beginning": "20:00", "end": "22:00"}],
            },
            {
                "dayofweek": 3,
                "local_date": "2018-06-13",
                "status": "open",
                "opening_hours": [{"beginning": "20:00", "end": "22:00"}],
            },
            {
                "dayofweek": 4,
                "local_date": "2018-06-14",
                "status": "open",
                "opening_hours": [{"beginning": "20:00", "end": "22:00"}],
            },
            {
                "dayofweek": 5,
                "local_date": "2018-06-15",
                "status": "open",
                "opening_hours": [{"beginning": "20:00", "end": "22:00"}],
            },
            {
                "dayofweek": 6,
                "local_date": "2018-06-16",
                "status": "open",
                "opening_hours": [{"beginning": "20:00", "end": "22:00"}],
            },
            {
                "dayofweek": 7,
                "local_date": "2018-06-17",
                "status": "open",
                "opening_hours": [
                    {"beginning": "12:00", "end": "14:00"},
                    {"beginning": "20:00", "end": "22:00"},
                ],
            },
        ],
    )


@freeze_time("2018-06-14 21:30:00", tz_offset=0)
def test_happy_hour_over():
    """
    The POI should already be closed since it's 21h30 UTC while
    the POI closes at 22h00 in UTC+3.
    """
    hh_block = get_moscow_poi("Mo-Su 10:00-22:00")

    assert hh_block.status == "closed"
    assert hh_block.next_transition_datetime == "2018-06-15T10:00:00+03:00"
    assert hh_block.seconds_before_next_transition == 34200
    assert hh_block.raw == "Mo-Su 10:00-22:00"
    assert len(hh_block.days) == 7
    assert all(d.status == "open" for d in hh_block.days)
