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
    freezer = freeze_time("2018-06-14 9:30:00")
    freezer.start()

    response = OpeningHourBlock.from_es(
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

    assert response == OpeningHourBlock(
        status='open',
        next_transition_time='2018-06-14T22:00:00+00:00',
        seconds_before_next_transition=45000,
        is_24_7=False,
        raw='Mo-Su 10:00-22:00',
        days=[]
    )

    freezer.stop()
