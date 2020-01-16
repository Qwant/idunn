"""
Bragi parameters as defined here:
  https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/routes/autocomplete.rs#L59
"""
from enum import Enum
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel, PositiveInt, confloat, conint

from idunn import settings
from .cosmogony import ZoneType


class Type(str, Enum):
    City = "city"
    House = "house"
    Poi = "poi"
    StopArea = "public_transport:stop_area"
    Street = "street"
    Zone = "zone"


class QueryParams(BaseModel):
    q: str
    lon: Optional[confloat(ge=-180, le=180)]
    lat: Optional[confloat(ge=-90, le=90)]
    lang: str
    limit: PositiveInt
    pt_dataset: List[str]
    poi_dataset: List[str]
    all_data: bool
    offset: conint(gt=-1)
    timeout: Optional[conint(gt=-1)]
    type: List[Type]
    zone_type: List[ZoneType]
    poi_type: List[str]
    _debug: bool

    def __init__(
        self,
        q: str = Query(..., title="query string"),
        lon: Optional[float] = Query(None, ge=-180, le=180, title="latitude for the focus"),
        lat: Optional[float] = Query(None, ge=-90, le=90, title="longitude for the focus"),
        lang: str = Query(settings["DEFAULT_LANGUAGE"], title="language"),
        limit: PositiveInt = 10,
        pt_dataset: List[str] = Query([]),
        poi_dataset: List[str] = Query([]),
        all_data: bool = False,
        offset: conint(gt=-1) = 0,
        timeout: Optional[conint(gt=-1)] = None,
        type: List[Type] = Query([]),
        zone_type: List[ZoneType] = Query([]),
        poi_type: List[str] = Query([]),
        _debug: bool = False,
    ):
        super().__init__(
            q=q,
            lon=lon,
            lat=lat,
            lang=lang,
            limit=limit,
            pt_dataset=pt_dataset,
            poi_dataset=poi_dataset,
            all_data=all_data,
            offset=offset,
            timeout=timeout,
            type=type,
            zone_type=zone_type,
            poi_type=poi_type,
            _debug=_debug,
        )


class ExtraParams(BaseModel):
    shape: dict = Query(None, title="restrict search inside of a polygon")
