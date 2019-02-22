import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import get_geom, get_name, fetch_bbox_places, LONG, SHORT, DEFAULT_VERBOSITY_LIST

from apistar import http
import json

from pydantic import BaseModel, ValidationError, validator
from typing import List, Optional

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

MAX_WIDTH = 1.0 # max longitude in degrees
MAX_HIGH = 1.0  # max latitude in degrees

class PlacesQueryParam(BaseModel):
    bbox: str
    raw_filter: str
    size: Optional[int] = None
    lang: str = None
    verbosity: str = DEFAULT_VERBOSITY_LIST

    @validator('lang', pre=True, always=True)
    def valid_lang(cls, v):
        from app import settings
        if v is None:
            v = settings['DEFAULT_LANGUAGE']
        return v.lower()

    @validator('verbosity', pre=True, always=True)
    def valid_verbosity(cls, v):
        if v not in VERBOSITY_LEVELS:
            raise ValueError(f"the verbosity: \'{v}\' does not belong to possible verbosity levels: {VERBOSITY_LEVELS}")
        return v

    @validator('bbox')
    def valid_bbox(cls, v):
        v = v.split(',')
        if len(v) != 4:
            raise ValueError('the bbox is incomplete')
        left, bot, right, top = float(v[0]), float(v[1]), float(v[2]), float(v[3])
        if left > right or bot > top or (right - left > MAX_WIDTH) or (top - bot > MAX_HIGH):
            raise ValueError('the bbox dimensions are invalid')
        return v

    @validator('size', always=True)
    def max_size(cls, v):
        from app import settings
        max_size = settings['LIST_PLACES_MAX_SIZE']
        sizes = [v, max_size]
        return min(int(i) for i in sizes if i is not None)

    @validator('raw_filter', always=True)
    def valid_raw_filter(cls, v):
        if "," not in v:
            raise ValueError(f"raw_filter \'{v}\' is invalid")
        return v

def get_places_bbox(bbox, es: Elasticsearch, indices: IndexNames, settings: Settings, query_params: http.QueryParams):
    places_list = []

    try:
        params = PlacesQueryParam(**query_params)
    except ValidationError as e:
        logger.warning(f"Validation Error: {e.json()}")
        raise BadRequest(
            detail={"message": e.errors()}
        )

    bbox_places = fetch_bbox_places(
        es,
        indices,
        categories = query_params.get_list('raw_filter'),
        bbox = params.bbox,
        max_size = params.size
    )

    for p in bbox_places:
        poi = POI.load_place(
            p['_source'],
            params.lang,
            settings,
            params.verbosity
        )
        places_list.append(poi)

    return {
        "places": places_list
    }
