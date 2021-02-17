from idunn.blocks import AnyBlock
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class PlaceMeta(BaseModel):
    source: Optional[str]
    source_url: Optional[str] = Field(description="URL to the place details at the source")
    contribute_url: Optional[str] = Field(
        description="Url to edit place details. Defined for OSM POIs only."
    )
    maps_place_url: HttpUrl = Field(description="Direct URL to the place details on Qwant Maps.")
    maps_directions_url: HttpUrl = Field(
        description=(
            "Direct URL to the directions on Qwant Maps, with the current place selected as "
            "destination."
        )
    )


class Street(BaseModel):
    id: Optional[str]
    name: Optional[str]
    label: Optional[str]
    postcodes: Optional[List[str]]


class AdministrativeRegion(BaseModel):
    id: Optional[str]
    name: Optional[str]
    label: Optional[str]
    class_name: Optional[str]
    postcodes: Optional[List[str]]


class AdministrativeRegionContext(BaseModel):
    label: Optional[str]


class Address(BaseModel):
    id: Optional[str]
    name: Optional[str]
    label: Optional[str]
    housenumber: Optional[str]
    street: Optional[Street]
    postcode: Optional[str]
    admins: Optional[List[AdministrativeRegion]]
    admin: Optional[AdministrativeRegionContext]
    country_code: Optional[str]


class Place(BaseModel):
    type: str
    id: Optional[str]
    name: Optional[str]
    local_name: Optional[str]
    class_name: Optional[str]
    subclass_name: Optional[str]
    geometry: Optional[dict]
    address: Optional[Address]
    blocks: List[AnyBlock]
    meta: PlaceMeta
