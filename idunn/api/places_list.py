import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.utils.categories import Categories
from idunn.places import POI
from idunn.api.utils import fetch_bbox_places, LONG, SHORT, DEFAULT_VERBOSITY_LIST

from apistar import http

from pydantic import BaseModel, ValidationError, validator
from pydantic.error_wrappers import ErrorWrapper
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

MAX_WIDTH = 1.0 # max bbox longitude in degrees
MAX_HEIGHT = 1.0  # max bbox latitude in degrees

ALL_CATEGORIES = None

def init_categories(categories):
    global ALL_CATEGORIES
    if ALL_CATEGORIES is None:
        ALL_CATEGORIES = categories.get('categories')

class PlacesQueryParam(BaseModel):
    bbox: str
    raw_filter: Optional[List[str]]
    category: Optional[List[str]]
    size: Optional[int] = None
    lang: str = None
    verbosity: str = DEFAULT_VERBOSITY_LIST

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.raw_filter is None and self.category is None:
            exc = ValueError("At least one \'raw_filter\' or one \'category\' parameter is required")
            raise ValidationError([ErrorWrapper(exc, loc='PlacesQueryParam')])

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
            raise ValueError('bbox should contain 4 numbers')
        left, bot, right, top = float(v[0]), float(v[1]), float(v[2]), float(v[3])
        if left > right or bot > top:
            raise ValueError('bbox dimensions are invalid')
        if (right - left > MAX_WIDTH) or (top - bot > MAX_HEIGHT):
            raise ValueError('bbox is too large')
        return v

    @validator('size', always=True)
    def max_size(cls, v):
        from app import settings
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

    @validator('category', whole=True)
    def flat_categories(cls, v):
        return [filt for filters in v for filt in filters]

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

def get_places_bbox(bbox, es: Elasticsearch, categories: Categories, indices: IndexNames, settings: Settings, query_params: http.QueryParams):
    init_categories(categories)
    raw_params = get_raw_params(query_params)
    try:
        params = PlacesQueryParam(**raw_params)
    except ValidationError as e:
        logger.warning(f"Validation Error: {e.json()}")
        raise BadRequest(
            detail={"message": e.errors()}
        )

    bbox_places = fetch_bbox_places(
        es,
        indices,
        categories = params.raw_filter or params.category,
        bbox = params.bbox,
        max_size = params.size
    )

    places_list = []
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
