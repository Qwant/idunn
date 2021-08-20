"""
Based on models generated by datamodel-codegen from pagesjaunes OpenApi spec:
https://developer.pagesjaunes.fr/portals/api/sites/solocal-testdeveloper/liveportal/apis/businessinfossandbox/download_spec
"""

import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


class BusinessDescription(BaseModel):
    """
    Omitted fields:
      - label: Business description label
    """

    values: List[str] = Field([], description="Array of Business description values")


class Category(BaseModel):
    category_name: Optional[str] = Field(None, description="Category name")


class ContactType(Enum):
    MOBILE = "MOBILE"
    TELEPHONE = "TELEPHONE"
    TELEPHONE_FAX = "TELEPHONE_FAX"
    FAX = "FAX"
    TELEX = "TELEX"
    MAIL = "MAIL"
    MINITEL = "MINITEL"
    AUTRE = "AUTRE"


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


class TransactionalLinkType(Enum):
    COMMANDER_CHRONO = "COMMANDER_CHRONO"
    COMMANDER = "COMMANDER"
    INSTANT_MESSAGING = "INSTANT_MESSAGING"
    PRENDRE_RDV_CLIC_RDV = "PRENDRE_RDV_CLIC_RDV"
    PRENDRE_RDV_EXTERNE = "PRENDRE_RDV_EXTERNE"
    PRENDRE_RDV_INTERNE = "PRENDRE_RDV_INTERNE"
    QUOTATION_REQUEST = "QUOTATION_REQUEST"
    RESERVER_ACCOR = "RESERVER_ACCOR"
    RESERVER_INTERNE = "RESERVER_INTERNE"
    RESERVER_LA_FOURCHETTE_PROMO = "RESERVER_LA_FOURCHETTE_PROMO"
    RESERVER_LA_FOURCHETTE = "RESERVER_LA_FOURCHETTE"
    RESERVER_LA_FOURCHETTE_SIMPLE = "RESERVER_LA_FOURCHETTE_SIMPLE"
    RESERVER = "RESERVER"


class TransactionalLink(BaseModel):
    type: Optional[TransactionalLinkType] = Field(None, description="URL of the transactional link")
    url: Optional[str] = Field(None, description="URL of the transactional link")
    next_free_slot: Optional[str] = Field(None, description="Next free slot for an appointment")

    @validator("type", pre=True)
    def validate_type(cls, field: str):
        try:
            return TransactionalLinkType(field)
        except ValueError:
            logger.warning("Got unknown transactional type from pagesjaunes: %s", field)
            return None


class Photo(BaseModel):
    """
    Omitted fields:
      - description: The photo description
    """

    url: Optional[str] = Field(None, description="URL of the photo")


class Reviews(BaseModel):
    total_reviews: int = Field(
        description="Number of reviews that have been written for this listing"
    )
    overall_review_rating: float = Field(description="Overall rating for the review")


class Schedules(BaseModel):
    """
    Omitted fields:
      - opening_days: Array of opening days
      - closing_periods: Array of closing periods
      - exceptional_opening_days: Array of exceptional opening days
      - exceptional_closing_days: Array of exceptional closing days
    """

    opening_hours: Optional[str] = Field(None, description="Opening hours")


class Urls(BaseModel):
    """
    Omitted fields:
      - map_url: Link to the map URL on PagesJaunes.fr
      - immersive_url: Link to the immersive view on PagesJaunes.fr
      - itinerary_url: Link to the detailed route to that place.fr
    """

    merchant_url: Optional[str] = Field(
        None, description="Link to the merchant page on PagesJaunes.fr"
    )
    reviews_url: Optional[str] = Field(
        None, description="Link to the business reviews on PagesJaunes.fr"
    )


class UrlType(Enum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    LINKEDIN = "LINKEDIN"
    MINISITE = "MINISITE"
    PINTEREST = "PINTEREST"
    SITE_EXTERNE = "SITE_EXTERNE"
    SITE_PRIVILEGE = "SITE_PRIVILEGE"
    TWITTER = "TWITTER"
    WEBSITE = "WEBSITE"
    YOUTUBE = "YOUTUBE"


class WebsiteUrl(BaseModel):
    url_type: Optional[UrlType] = Field(None, description="URL type of merchant website")
    website_url: Optional[str] = Field(None, description="URL of merchant website")
    suggested_label: Optional[str] = Field(None, description="Suggested label of merchant website")

    @validator("url_type", pre=True)
    def validate_url_type(cls, field: str):
        try:
            return UrlType(field)
        except ValueError:
            logger.warning("Got unknown url type from pagesjaunes: %s", field)
            return None


class Inscription(BaseModel):
    """
    Omitted fields:
      - label: Name of one business subscription
      - address_district: District of business location
      - address_postal_box: Postal box of business location
    """

    address_street: Optional[str] = Field(
        None, description="Number and street of business location"
    )
    address_zipcode: Optional[str] = Field(None, description="Zip code of business location")
    address_city: Optional[str] = Field(None, description="City of business location")
    latitude: Optional[float] = Field(None, description="Location latitude (WGS84)")
    longitude: Optional[float] = Field(None, description="Location longitude (WGS84)")
    reviews: Optional[Reviews] = Field(None, description="Review object")
    contact_infos: List[ContactInfo] = Field([], description="Array of contact information")
    urls: Optional[Urls] = Field(None, description="Wraps the set of urls for this business")


class RestaurantInfo(BaseModel):
    """
    Omitted fields:
      - type: cooking type
      - cooking_convictions: Cooking convictions
    """

    atmospheres: List[str] = Field([], description="Atmospheres")


class AccommodationInfo(BaseModel):
    """
    Omitted fields:
      - type: Type of accommodation information
      - rate_base: Rate base of the accommodation information
    """

    category: Optional[str] = Field(None, description="Categorie of the accommodation information")


class Response(BaseModel):
    """
    Omitted fields:
      - listing_id: Id of the bloc of the professional
      - business_website: Business website object
      - videos: Array of videos
      - legal_notices: Array of legal notices
      - payment_types: Array of payment types
      - current_status: Current status
      - nearby_stations: Array of nearby stations
      - b2b: Legal and financial informations
      - products: Array of products
      - healthcare: Healthcare informations
      - eco_responsibility: Eco responsability informations
    """

    merchant_id: Optional[str] = Field(None, description="Id of the professional")
    merchant_name: Optional[str] = Field(None, description="Name of the professional")
    description: Optional[str] = Field(None, description="The professional ’s description")
    thumbnail_url: Optional[str] = Field(None, description="URL of the professional ’s thumbnail")
    website_urls: List[WebsiteUrl] = Field([], description="Array of merchant websites URLs")
    business_descriptions: List[BusinessDescription] = Field(
        [], description="Array of business description object"
    )
    photos: List[Photo] = Field([], description="Array of photos")
    categories: List[Category] = Field([], description="Array of categories")
    restaurant_info: Optional[RestaurantInfo] = Field(None, description="Restaurant information")
    accommodation_infos: List[AccommodationInfo] = Field(
        [], description="Array of accommodation information"
    )
    schedules: Optional[Schedules] = Field(
        None,
        description=(
            "Schedules object "
            "(see http://wiki.openstreetmap.org/wiki/Key:opening_hours/specification to calculate "
            "current status)"
        ),
    )
    transactionals_links: List[TransactionalLink] = Field(
        [], description="Array of transactionals links"
    )
    inscriptions: List[Inscription] = Field(
        [], description="Array of all subscriptions (contact info and address) for a business"
    )
