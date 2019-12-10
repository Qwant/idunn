from idunn.blocks.base import BlocksValidator
from idunn.api.utils import LONG, BLOCKS_BY_VERBOSITY
from pydantic import BaseModel
from typing import ClassVar, Optional


class PlaceMeta(BaseModel):
    source: Optional[str]


class Place(BaseModel):
    type: str
    id: Optional[str]
    name: Optional[str]
    local_name: Optional[str]
    class_name: Optional[str]
    subclass_name: Optional[str]
    geometry: Optional[dict]
    address: Optional[dict]
    blocks: ClassVar = BlocksValidator(allowed_blocks=BLOCKS_BY_VERBOSITY.get(LONG))
    meta: PlaceMeta
