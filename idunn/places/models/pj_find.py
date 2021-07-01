# Based on models generated by datamodel-codegen from pagesjaunes OpenApi spec:
# https://developer.pagesjaunes.fr/docs/findbusinesssandbox/1/overview

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .pj_info import TransactionalLink, WebsiteUrl


class BusinessDescription(BaseModel):
    """
    Omitted fields:
      - label: Business description label
    """

    values: List[str] = Field([], description="Array of Business description values")


class Category(BaseModel):
    category_name: Optional[str] = Field(None, description="Category name")


class ContactType(Enum):
    TELEPHONE = "TELEPHONE"
    TELEPHONE_FAX = "TELEPHONE_FAX"
    FAX = "FAX"
    TELEX = "TELEX"
    MAIL = "MAIL"
    AUTRE = "AUTRE"
    MOBILE = "MOBILE"


class ContactInfo(BaseModel):
    """
    Omitted fields:
      - phone_number_pricing: Phone number pricing
      - phone_number_pricing_type: Type of phone number pricing
      - phone_number_details: Details of phone number
      - no_direct_marketing: No direct marketing allowed for this business
    """

    contact_type: Optional[ContactType] = Field(None, description="Type of contact information")
    contact_value: Optional[str] = Field(
        None, description="Contact information: Phone number (not formatted), Email..."
    )


class Pages(BaseModel):
    """
    Omitted fields:
      - current_page: Current page
      - page_count: Total number of pages
      - listings_per_page: Listings per page
      - prev_page_url: URL to the previous page
      - current_page_url: URL to the current page
    """

    next_page_url: Optional[str] = Field(None, description="URL to the next page")


class Reviews(BaseModel):
    total_reviews: int = Field(
        description="Number of reviews that have been written for this listing"
    )
    overall_review_rating: float = Field(description="Overall rating for the review")


class Urls(BaseModel):
    """
    Omitted fields:
      - map_url: Link to the map URL on PagesJaunes.fr
      - immersive_url: (Deprecated) Link to the immersive view on PagesJaunes.fr
      - itinerary_url: Link to the detailed route to that place.fr
    """

    merchant_url: Optional[str] = Field(
        None, description="Link to the merchant page on PagesJaunes.fr"
    )
    reviews_url: Optional[str] = Field(
        None, description="Link to the business reviews on PagesJaunes.fr"
    )


class Context(BaseModel):
    """
    Omitted fields:
      - search: Search parameter context object
      - results: Results listing summary object
    """

    pages: Optional[Pages] = Field(None, description="Paging context object")


class Inscription(BaseModel):
    """
    Omitted fields:
      - inscription_id: Id of one business subscription
      - pro_id: Id of the professional site
      - label: Name of one business subscription
      - adress_street: (Deprecated) Number and street of business location
      - adress_zipcode: (Deprecated) Zip code of business location
      - adress_city: (Deprecated) City of business location
      - distance: Distance from center (in m), in case of proximity search
    """

    address_street: Optional[str] = Field(
        None, description="Number and street of business location"
    )
    address_zipcode: Optional[str] = Field(None, description="Zip code of business location")
    address_city: Optional[str] = Field(None, description="City of business location")
    latitude: Optional[float] = Field(None, description="Location latitude (WGS84)")
    longitude: Optional[float] = Field(None, description="Location longitude (WGS84)")
    reviews: Optional[Reviews] = Field(None, description="Reviews object")
    contact_info: List[ContactInfo] = Field([], description="Array of contact information")
    urls: Optional[Urls] = Field(None, description="Wraps the set of urls for this business")


class Listing(BaseModel):
    """
    Omitted fields:
      - listing_id: Listing id
      - position: Listing position (for stats purpose)
      - visuel_url: List of visuels URL
      - description: (Deprecated) Descriptive text
      - business_website: Array of business website object
      - eco_label: Eco-responsibility label
      - legal_notice: Array of legal notices
      - current_status: (Deprecated) Type current status
      - healthcare: Healthcare informations
      - services: Services
      - certifications: Certifications
    """

    merchant_id: Optional[str] = Field(
        None, description="The merchant id, identifying the business"
    )
    merchant_name: Optional[str] = Field(None, description="Name of the merchant")
    thumbnail_url: Optional[str] = Field(None, description="URL for the merchant main thumbnail")
    website_urls: List[WebsiteUrl] = Field([], description="Array of merchant websites URLs")
    business_descriptions: List[BusinessDescription] = Field(
        [], description="Array of business description object"
    )
    categories: List[Category] = Field([], description="Array of categories")
    inscriptions: List[Inscription] = Field(
        [], description="Array of all subscriptions (contact info and address) for a business"
    )
    opening_hours: Optional[str] = Field(
        None,
        description=(
            "Opening hours "
            "(see http://wiki.openstreetmap.org/wiki/Key:opening_hours/specification to calculate "
            "current status)"
        ),
    )
    transactionals_links: List[TransactionalLink] = Field(
        [], description="Array of transactionals links"
    )


class SearchResults(BaseModel):
    """
    Omitted fields:
      - search_url: URL to the search results on PagesJaunes.fr (only if
        coordinates not used in query)
      - small_map_url: URL for small map image
    """

    listings: List[Listing] = Field([], description="Array of listings")


class Response(BaseModel):
    context: Optional[Context] = Field(
        None, description="object containing the context data for this query"
    )
    search_results: Optional[SearchResults] = Field(
        None, description="Object containing the search result for this query"
    )
