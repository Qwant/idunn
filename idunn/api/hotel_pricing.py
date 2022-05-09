import json
from enum import Enum
from typing import Optional

from fastapi import Depends, Query
from pydantic import BaseModel

from idunn import settings
from idunn.datasources.tripadvisor import Tripadvisor
from idunn.places.models.ta_api_reponse import HotelPricingResponse


class HotelIdType(Enum):
    TRIPADVISOR = "TA"
    HOTELS = "EAN"
    PRICELINE = "PCLN"
    BOOKING = "BCOM"
    EXPEDIA = "EXPE"


class CommonQueryParam(BaseModel):
    key: str = Query(
        settings.get("TA_API_KEY"),
        description="Access key to the API. "
        "This value is provided by your Tripadvisor Account Manager",
    )
    check_in: str = Query(None, description="The check-in date in the YYYY-MM-DD format")
    check_out: str = Query(None, description="The check-out date in the YYYY-MM-DD format")
    user_agent: str = Query(
        None,
        description="When making this request client side set this value to 'infer'"
        " and the service will automatically resolve the user-agent",
    )
    ip_address: str = Query(
        None,
        description="When making this request client side, set this value to 'infer' "
        "and the service will automatically resolve the user-agent",
    )
    num_adults: Optional[int] = Query(
        None,
        description="The total number of adults that will stay at the accommodation."
        " Supported values are between 1 to 4. The default value is '1'",
    )
    num_rooms: Optional[int] = Query(
        None, description="The number of rooms to be booked. Supported values are between 1 to 8"
    )
    currency: Optional[str] = Query(
        None,
        description="The currency code to be used to display prices. "
        "It should follow ISO 4217 format. The default value is 'USD'",
    )
    locale: Optional[str] = Query(
        None,
        description="The Preferred locale for the current request following the RFC 3066 format",
    )
    custom_tracking_var1: Optional[str] = Query(
        None,
        description="The Preferred locale for the current request following the RFC 3066 format",
    )


class SearchHotelByLocationParam(CommonQueryParam):
    location_id: str = Query(
        None,
        description="The Tripadvisor location ID of"
        " the location for which you are requesting hotels",
    )
    limit: Optional[int] = Query(
        None, description="The maximum number of hotels to return for the given location"
    )


class SearchHotelByIdParam(CommonQueryParam):
    hotel_ids: str = Query(
        None,
        description="Unique IDs of the hotel (s) for which you are requesting pricing."
        " Used in conjuction with hotel_id_type",
    )
    hotel_id_type: Optional[HotelIdType] = Query(
        None,
        description="The hotel ID type for corresponding hotel_id. "
        "If not provided, defaults to Tripadvisor hotel ID",
    )


async def get_hotel_pricing(params: SearchHotelByIdParam = Depends()) -> HotelPricingResponse:
    """Get availability and price for a given hotel Id with TripAdvisor api"""
    return await Tripadvisor().get_hotel_pricing_by_hotel_id(json.loads(params.json()))
