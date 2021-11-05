from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Error(BaseModel):
    code: Optional[int] = Field(None, description="Error code")
    messageKey: Optional[str] = Field(None, description="An array of hotels")
    message: Optional[str] = Field(None, description="Error message")


class Availability(Enum):
    pending = "pending"
    available = "available"
    unavailable = "unavailable"
    unknown = "unknown"


class Offer(BaseModel):
    availability: Optional[str] = Field(
        None,
        description="The availability of the offer. "
        "Possible values are 'pending', 'available', 'unavailable', 'unknown'",
    )
    displayName: Optional[str] = Field(
        None, description="The display name for the offer provider, eg. Tripadvisor"
    )
    displayPrice: Optional[str] = Field(
        None, description="The price to show to the user with a currency symbol"
    )
    price: Optional[int] = Field(
        None, description="The price to show to the user represented as a number"
    )
    logo: Optional[str] = Field(None, description="The URL of the Tripadvisor logo")
    clickUrl: Optional[str] = Field(
        None, description="The URL to the Tripadvisor /HotelHighlight page with offers"
    )


class Hotel(BaseModel):
    hotelId: Optional[str] = Field(None, description="A unique ID associated with the hotel")
    strikeThroughDisplayPrice: Optional[str] = Field(
        None, description="The strike through pricing for the hotel."
    )
    availability: Optional[Availability] = Field(
        None,
        description="The availability of the hotel. Possible values "
        "are 'pending', 'available', 'unavailable', 'unknown'",
    )
    offers: Optional[List[Offer]] = Field(
        [],
        description="An array of offers for the given hotel (see below)."
        " The size of the array should be 1",
    )


class Success(BaseModel):
    requestId: Optional[str] = Field(
        None,
        description="A unique ID associated with the request. This will be regenerated "
        "for every new request and reuse for the following polling requests",
    )
    results: Optional[List[Hotel]] = Field([], description="An array of hotels")
    isComplete: Optional[bool] = Field(
        None, description="Indicates if the response is complete or if polling is required."
    )
    pollingLink: Optional[str] = Field(
        None,
        description="Url to make a polling request for the same search data."
        " This allows us to serve the same request with additional pricing information."
        " This link is only returned when the response is incomplete",
    )


class HotelPricingResponse(BaseModel):
    success: Optional[Success] = Field(None, description="Success")
    errors: Optional[Error] = Field(None, description="Errors")
    warnings: Optional[List[str]] = Field(None, description="Warning")
    completedAt: Optional[str] = Field(None, description="Complete request date")
