"""
Implement GeocodeJson specification as defined here:
 - https://github.com/geocoders/geocodejson-spec/tree/master/draft
 - https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/model.rs
"""
from typing import List, Optional, Tuple

from pydantic import BaseModel, PositiveInt, confloat

from .cosmogony import ZoneType

from enum import Enum


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


class Explanation(BaseModel):
    value: float
    description: str
    details: List["Explanation"]


class Context(BaseModel):
    explanation: Optional[Explanation]


class Feature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: FeatureProperties

    # From CanalTP/mimirsbrunn:libs/bragi/src/model.rs
    distance: Optional[PositiveInt]
    context: Optional[Context]


class IntentionType(str, Enum):
    Brand = "brand"
    LocCity = "loc_city"
    ObjetBD = "objetBD"
    Attraction = "attraction"


class TagType(str, Enum):
    Brand = "brand"
    LocCity = "loc_city"
    ObjetBD = "objetBD"
    Attraction = "attraction"
    Hotel = "hotel"
    TrainStation = "train_station"
    Restaurant = "restaurant"


class Intention(BaseModel):
    type: str = IntentionType
    intention: TagType
    query_phrase: str


class Geocoding(BaseModel):
    version: str = "0.1.0"
    licence: Optional[str]
    attribution: Optional[str]
    query: Optional[str]


class IdunnAutocomplete(BaseModel):
    type: str = "FeaturesCollection"
    geocoding: Geocoding = Geocoding()
    intentions: Optional[List[Intention]]
    features: List[Feature]


GeocodingResponse.update_forward_refs()
Explanation.update_forward_refs()
