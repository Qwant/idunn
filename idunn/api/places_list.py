import os
import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn import settings
from idunn.utils.settings import Settings, _load_yaml_file
from idunn.utils.index_names import IndexNames
from idunn.places import POI, PjPOI
from idunn.api.utils import fetch_bbox_places, LONG, SHORT, DEFAULT_VERBOSITY_LIST
from .pages_jaunes import pj_source

from apistar import http

from pydantic import BaseModel, ValidationError, validator
from pydantic.error_wrappers import ErrorWrapper
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

MAX_WIDTH = 1.0 # max bbox longitude in degrees
MAX_HEIGHT = 1.0  # max bbox latitude in degrees


def get_categories():
    categories_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml")
    return _load_yaml_file(categories_path)['categories']

ALL_CATEGORIES = get_categories()

class PlacesQueryParam(BaseModel):
    bbox: str
    raw_filter: List[str] = None
    category: List[Any] = None
    size: Optional[int] = None
    lang: str = None
    verbosity: str = DEFAULT_VERBOSITY_LIST

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.raw_filter and not self.category:
            exc = ValueError("At least one \'raw_filter\' or one \'category\' parameter is required")
            raise ValidationError([ErrorWrapper(exc, loc='PlacesQueryParam')])

    @validator('lang', pre=True, always=True)
    def valid_lang(cls, v):
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
            raise ValueError('bbox should contain 4 numbers')
        left, bot, right, top = float(v[0]), float(v[1]), float(v[2]), float(v[3])
        if left > right or bot > top:
            raise ValueError('bbox dimensions are invalid')
        if (right - left > MAX_WIDTH) or (top - bot > MAX_HEIGHT):
            raise ValueError('bbox is too large')
        return (left, bot, right, top)

    @validator('size', always=True)
    def max_size(cls, v):
        max_size = settings['LIST_PLACES_MAX_SIZE']
        sizes = [v, max_size]
        return min(int(i) for i in sizes if i is not None)

    @validator('raw_filter')
    def valid_raw_filter(cls, v):
        if "," not in v:
            raise ValueError(f"raw_filter \'{v}\' is invalid")
        return v

    @validator('category')
    def valid_category(cls, v):
        if v not in ALL_CATEGORIES:
            raise ValueError(f"Category \'{v}\' is invalid since it does not belong to the set of possible categories: {list(ALL_CATEGORIES.keys())}")
        else:
            v = ALL_CATEGORIES.get(v)
        return v

def get_raw_params(query_params):
    raw_params = dict(query_params)
    if 'category' in query_params:
        raw_params['category'] = query_params.get_list('category')
    if 'raw_filter' in query_params:
        raw_params['raw_filter'] = query_params.get_list('raw_filter')
    if raw_params.get('raw_filter') and raw_params.get('category'):
        raise BadRequest(
            detail={"message": "Both \'raw_filter\' and \'category\' parameters cannot be provided together"}
        )
    return raw_params

def get_places_bbox(bbox, es: Elasticsearch, indices: IndexNames, settings: Settings, query_params: http.QueryParams):
    raw_params = get_raw_params(query_params)
    try:
        params = PlacesQueryParam(**raw_params)
    except ValidationError as e:
        logger.warning(f"Validation Error: {e.json()}")
        raise BadRequest(
            detail={"message": e.errors()}
        )

    if params.category \
        and all(c.get('pj_filters') for c in params.category) \
        and pj_source.bbox_is_covered(params.bbox) :
        all_categories = [pj_category for c in params.category for pj_category in c['pj_filters']]
        places_list = pj_source.get_places_bbox(all_categories, params.bbox, size=params.size)
    else:
        if params.raw_filter:
            raw_filters = params.raw_filter
        else:
            raw_filters = [f for c in params.category for f in c['raw_filters']]

        bbox_places = fetch_bbox_places(
            es,
            indices,
            raw_filters=raw_filters,
            bbox=params.bbox,
            max_size=params.size
        )
        places_list = [POI(p['_source']) for p in bbox_places]

    return {
        "places": [p.load_place(params.lang, params.verbosity) for p in places_list]
    }
