from app import app
from freezegun import freeze_time
from apistar.test import TestClient
from idunn.blocks.opening_hour import OpeningHourBlock

def test_opening_hour():
    """
    Test that the opening_hours block for a POI located
    in a different timezone (Moscow) contains the correct
    information.
    """
    client = TestClient(app)
    with freeze_time("2018-06-14 9:30:00", tz_offset=1):
        """
        We freeze time at 9h30 Paris
        (ie. 8h30 UTC, 11h30 Moscow)
        The POI located in Moscow should be open since
        the local time is 11h30.

        We create a fake OpeningHourBlock from a
        raw json extracted from a POI located in
        Moscow city.
        """
        oh_block = OpeningHourBlock.from_es(
            {
                "coord": {
                    "lon": 37.588161523500276,
                    "lat": 55.74831406552745
                },
                "properties": {
                    "opening_hours": "Mo-Su 10:00-22:00"
                }
            },
            lang='en'
        )

        """
        We check especially here the status, next_transition_datetime,
        seconds_before_next_transition are correct.
        """
        assert oh_block == OpeningHourBlock(
            status='open',
            next_transition_datetime='2018-06-14T22:00:00+03:00',
            seconds_before_next_transition=34200,
            is_24_7=False,
            raw='Mo-Su 10:00-22:00',
            days=[]
        )
