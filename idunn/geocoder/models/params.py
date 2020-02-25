"""
Bragi parameters as defined here:
  https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/routes/autocomplete.rs#L59
"""
from enum import Enum
from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel, Field, PositiveInt, confloat, conint
from pydantic.dataclasses import dataclass

from idunn import settings
from .cosmogony import ZoneType


class Type(str, Enum):
    # City = "city" # this field is available in Bragi but deprecated
    House = "house"
    Poi = "poi"
    StopArea = "public_transport:stop_area"
    Street = "street"
    Zone = "zone"


@dataclass
class QueryParams:
    q: str = Query(..., title="query string")
    lon: Optional[confloat(ge=-180, le=180)] = Query(None, title="latitude for the focus")
    lat: Optional[confloat(ge=-90, le=90)] = Query(None, title="longitude for the focus")
    lang: Optional[str] = Query(None, title="language")
    limit: PositiveInt = 10
    pt_dataset: List[str] = Query([])
    poi_dataset: List[str] = Query([])
    all_data: bool = False
    offset: conint(gt=-1) = 0
    timeout: Optional[conint(gt=-1)] = None
    type: List[Type] = Query([])
    zone_type: List[ZoneType] = Query([])
    poi_type: List[str] = Query([])

    nlu: bool = settings["AUTOCOMPLETE_NLU_DEFAULT"]

    def bragi_query_dict(self):
        """
        Return a dictionary similar to the result of self.dict() but rename
        arguments of type list with the suffix "[]", which is how they
        should be sent to bragi.
        """
        return {
            "q": self.q,
            "lon": self.lon,
            "lat": self.lat,
            "lang": self.lang,
            "limit": self.limit,
            "pt_dataset[]": self.pt_dataset,
            "poi_dataset[]": self.poi_dataset,
            "all_data": self.all_data,
            "offset": self.offset,
            "timeout": self.timeout,
            "type[]": self.type,
            "zone_type[]": self.zone_type,
            "poi_type[]": self.poi_type,
        }


class ExtraParams(BaseModel):
    shape: dict = Field(None, title="restrict search inside of a polygon")
