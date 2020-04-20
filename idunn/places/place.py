from idunn.blocks.base import BaseBlock, BlocksValidator
from idunn.api.utils import LONG, BLOCKS_BY_VERBOSITY
from pydantic import BaseModel
from typing import List, Optional


class PlaceMeta(BaseModel):
    source: Optional[str]


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
    blocks: List[BaseBlock] = BlocksValidator(allowed_blocks=BLOCKS_BY_VERBOSITY.get(LONG))
    meta: PlaceMeta
