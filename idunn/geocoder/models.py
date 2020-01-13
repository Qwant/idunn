"""
Implement GeocodeJson specification as defined here:
 - https://github.com/geocoders/geocodejson-spec/tree/master/draft
 - https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/model.rs
"""
import json

from enum import Enum
from typing import Any, List, Optional, Tuple

from pydantic import BaseModel, PositiveInt, confloat


Lon = confloat(ge=-180, le=180)
Lat = confloat(ge=-90, le=90)

Rect = Tuple[Lon, Lat, Lon, Lat]


class Coord(BaseModel):
    lon: Lon
    lat: Lat


class PoiType(BaseModel):
    id: str
    name: str


class CommercialMode(BaseModel):
    id: str
    name: str


class PhysicalMode(BaseModel):
    id: str
    name: str


class Network(BaseModel):
    id: str
    name: str


class Code(BaseModel):
    name: str
    value: str


class ZoneType(str, Enum):
    Suburb = "suburb"
    CityDistrict = "city_district"
    City = "city"
    StateDistrict = "state_district"
    State = "state"
    CountryRegion = "country_region"
    Country = "country"
    NonAdministrative = "non_administrative"


class AssociatedAdmin(BaseModel):
    id: str
    insee: str
    level: PositiveInt
    label: str
    name: str
    zip_codes: List[str]
    coord: Coord
    bbox: Optional[Rect]
    zone_type: Optional[ZoneType]
    parent_id: Optional[str]
    codes: List[Code]


class Line(BaseModel):
    id: str
    name: str
    code: Optional[str]
    color: Optional[str]
    text_color: Optional[str]
    commercial_mode: Optional[CommercialMode]
    network: Optional[Network]
    physical_modes: Optional[PhysicalMode]
    sort_order: Optional[PositiveInt]


class FeedPublished(BaseModel):
    id: str
    licence: str
    name: str
    url: str


class GeocodingProperty(BaseModel):
    key: str
    value: str


class Comment(BaseModel):
    name: str


class GeocodingResponse(BaseModel):
    type: str
    label: Optional[str]
    name: Optional[str]
    housenumber: Optional[str]
    street: Optional[str]
    locality: Optional[str]
    postcode: Optional[str]
    city: Optional[str]

    # The following fields are part of the GeocodeJson specification but are
    # currently disabled in Bragi:
    #  https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/model.rs#L194-L199
    #
    # accuracy: Optional[PositiveInt]
    # district: Optional[str]
    # country: Optional[str]
    # state: Optional[str]
    # country: Optional[str]
    # geohash: Optional[str]

    # From CanalTP/mimirsbrunn:libs/bragi/src/model.rs
    id: str
    zone_type: Optional[str]
    citycode: Optional[str]
    level: Optional[PositiveInt]
    administrative_regions: List[AssociatedAdmin]
    poi_types: List[PoiType] = []
    properties: List[GeocodingProperty] = []
    address: Optional["GeocodingResponse"]
    commercial_modes: List[CommercialMode] = []
    comments: List[Comment] = []
    physical_modes: List[PhysicalMode] = []
    lines: List[Line] = []
    timezone: Optional[str]
    codes: List[Code] = []
    feed_publishers: List[FeedPublished] = []
    bbox: Optional[Rect]
    country_codes: List[str] = []


class FeatureProperties(BaseModel):
    geocoding: GeocodingResponse


class Explaination(BaseModel):
    value: float
    description: str
    details: List["Explaination"]


class Context(BaseModel):
    explaination: Optional[Explaination]


class Feature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: FeatureProperties

    # From CanalTP/mimirsbrunn:libs/bragi/src/model.rs
    distance: Optional[PositiveInt]
    context: Optional[Context]


class Geocoding(BaseModel):
    version: str = "0.1.0"
    licence: Optional[str]
    attribution: Optional[str]
    query: Optional[str]


class GeocodeJson(BaseModel):
    type: str = "FeatureCollection"
    geocoding: Geocoding = Geocoding()
    features: List[Feature]


GeocodingResponse.update_forward_refs()
Explaination.update_forward_refs()
