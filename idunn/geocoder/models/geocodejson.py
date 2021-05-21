"""
Implement GeocodeJson specification as defined here:
 - https://github.com/geocoders/geocodejson-spec/tree/master/draft
 - https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/model.rs
"""
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, confloat, Field, validator

from idunn.api.constants import WIKIDATA_TO_BBOX_OVERRIDE
from .cosmogony import ZoneType


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
    level: int
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
    sort_order: Optional[int]


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


class GeocodingPlace(BaseModel):
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
    # https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/model.rs#L194-L199
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
    level: Optional[int]
    administrative_regions: List[AssociatedAdmin]
    poi_types: List[PoiType] = []
    properties: List[GeocodingProperty] = []
    address: Optional["GeocodingPlace"]
    commercial_modes: List[CommercialMode] = []
    comments: List[Comment] = []
    physical_modes: List[PhysicalMode] = []
    lines: List[Line] = []
    timezone: Optional[str]
    codes: List[Code] = []
    feed_publishers: List[FeedPublished] = []
    bbox: Optional[Rect]
    country_codes: List[str] = []

    @validator("bbox")
    def override_bbox(cls, v, values):
        if not v:
            return v
        codes = values["codes"]
        wikidata_id = next((c.value for c in codes if c.name == "wikidata"), None)
        if wikidata_id in WIKIDATA_TO_BBOX_OVERRIDE:
            return WIKIDATA_TO_BBOX_OVERRIDE[wikidata_id]
        return v


class FeatureProperties(BaseModel):
    geocoding: GeocodingPlace


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
    distance: Optional[int]
    context: Optional[Context]


class IntentionType(Enum):
    ADDRESS = "address"
    BRAND = "brand"
    CATEGORY = "category"
    POI = "poi"
    ANY_PLACE = "any_place"


class IntentionFilter(BaseModel):
    q: Optional[str]
    bbox: Optional[Rect]
    category: Optional[str]
    source: Optional[str]


class IntentionDescription(BaseModel):
    query: Optional[str]
    category: Optional[str]
    place: Optional[Feature]


class Intention(BaseModel):
    type: IntentionType
    filter: IntentionFilter = Field(
        ..., description="Filter params that can be passed to /places endpoint"
    )
    description: IntentionDescription = Field(
        ...,
        description=(
            "Details about the detected intention, useful to format a human-readable description"
        ),
    )


class Geocoding(BaseModel):
    version: str = "0.1.0"
    licence: Optional[str]
    attribution: Optional[str]
    query: Optional[str]


class IdunnAutocomplete(BaseModel):
    type: str = "FeatureCollection"
    geocoding: Geocoding = Geocoding()
    intentions: Optional[List[Intention]] = Field(None, description="Intentions detected by NLU.")
    features: List[Feature] = Field([], description="Geographic places matching the query.")


GeocodingPlace.update_forward_refs()
Explanation.update_forward_refs()
