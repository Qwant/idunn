from fastapi.testclient import TestClient
from .fixtures.api.tripadvisor_hotel_pricing import (
    mock_ta_search_by_hotel_id_api_with_the_hotel_captain_cook,
)
from app import app


def test_ta_pricing_hotel_api_success(mock_ta_search_by_hotel_id_api_with_the_hotel_captain_cook):
    client = TestClient(app)
    response = client.get(
        url="http://localhost/v1/hotel_pricing?hotel_ids=72177&check_in=2021-12-01&check_out=2021-12-03&ip_address=infer&user_agent=infer"
    )

    assert response.status_code == 200
    resp = response.json()

    assert resp["success"]["isComplete"] is True
    assert resp["success"]["pricingType"] == "base"

    assert len(resp["success"]["results"]) == 1
    result = resp["success"]["results"][0]
    assert result["hotelId"] == "72177"
    assert result["strikeThroughDisplayPrice"] == "$235"
    assert result["availability"] == "available"

    assert len(result["offers"]) == 1
    offer = result["offers"][0]
    assert offer["availability"] == "available"
    assert offer["displayName"] == "Tripadvisor"
    assert offer["displayPrice"] == "$235"
    assert offer["price"] == 235
    assert (
        offer["logo"]
        == "https://static.tacdn.com/img2/brand_refresh/Tripadvisor_logoset_solid_green.svg"
    )
    assert (
        offer["clickUrl"]
        == "https://www.tripadvisor.com/Hotel_Review-s1-g60880-d72177-Reviews-The_Hotel_Captain_Cook-Anchorage_Alaska.html?adults=1&inDay=1&inMonth=12&inYear=2021&m=66497&outDay=3&outMonth=12&outYear=2021&rooms=1&staydates=2021_12_01_2021_12_03"
    )
