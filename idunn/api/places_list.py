import os
import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest, HTTPException

from idunn import settings
from idunn.utils.settings import Settings, _load_yaml_file
from idunn.utils.index_names import IndexNames
from idunn.places import POI
from idunn.api.utils import fetch_bbox_places, DEFAULT_VERBOSITY_LIST, ALL_VERBOSITY_LEVELS
from idunn.places.event import Event
from .pages_jaunes import pj_source
from .constants import SOURCE_OSM, SOURCE_PAGESJAUNES
from .kuzzle import kuzzle_client

from apistar import http

from pydantic import BaseModel, ValidationError, validator
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

MAX_WIDTH = 1.0   # max bbox longitude in degrees
MAX_HEIGHT = 1.0  # max bbox latitude in degrees

ALL_SOURCES = [SOURCE_OSM, SOURCE_PAGESJAUNES]


def get_categories():
    categories_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml")
    return _load_yaml_file(categories_path)['categories']


def get_outing_types():
    outing_types_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml")
    return _load_yaml_file(outing_types_path)['outing_types']


ALL_CATEGORIES = get_categories()
ALL_OUTING_TYPES = get_outing_types()


class CommonQueryParam(BaseModel):
    bbox: str
    size: Optional[int] = None
    lang: str = None
    verbosity: str = DEFAULT_VERBOSITY_LIST

    @validator('lang', pre=True, always=True)
    def valid_lang(cls, v):
        if v is None:
            v = settings['DEFAULT_LANGUAGE']
        return v.lower()

    @validator('verbosity', pre=True, always=True)
    def valid_verbosity(cls, v):
        if v not in ALL_VERBOSITY_LEVELS:
            raise ValueError(f"the verbosity: \'{v}\' does not belong to possible verbosity levels: {VERBOSITY_LEVELS}")
        return v

    @validator('size', always=True)
    def max_size(cls, v):
        max_size = settings['LIST_PLACES_MAX_SIZE']
        sizes = [v, max_size]
        return min(int(i) for i in sizes if i is not None)

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


class PlacesQueryParam(CommonQueryParam):
    category: List[Any] = []
    raw_filter: List[str] = None
    source: Optional[str] = None
    q: Optional[str] = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.raw_filter and not self.category and not self.q:
            raise BadRequest({
                "message": "One of 'category', 'raw_filter' or 'q' parameter is required"
            })

    @validator('source')
    def valid_source(cls, v):
        if v not in ALL_SOURCES:
            raise ValueError(f"unknown source: '{v}'")
        return v

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


class EventQueryParam(CommonQueryParam):
    outing_types: str = None

    @validator('outing_types')
    def valid_outing_types(cls, v):
        if v not in ALL_OUTING_TYPES:
            raise ValueError(f"outing_types \'{v}\' is invalid since it does not belong to set of possible outings type: {list(ALL_OUTING_TYPES.keys())}")
        else:
            v = ALL_OUTING_TYPES.get(v, {})
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
        logger.info(f"Validation Error: {e.json()}")
        raise BadRequest(
            detail={"message": e.errors()}
        )

    source = params.source
    if source is None:
        if params.q:
            # PJ is currently the only source that accepts arbitrary queries
            source = SOURCE_PAGESJAUNES
        elif params.category \
            and all(c.get('pj_filters') for c in params.category) \
            and pj_source.bbox_is_covered(params.bbox):
            source = SOURCE_PAGESJAUNES
        else:
            source = SOURCE_OSM

    if source == SOURCE_PAGESJAUNES:
        all_categories = [pj_category for c in params.category for pj_category in c['pj_filters']]
        places_list = pj_source.get_places_bbox(all_categories, params.bbox, size=params.size, query=params.q)
    else:
        # Default source (OSM)
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
        "places": [p.load_place(params.lang, params.verbosity) for p in places_list],
        "source": source
    }


def get_events_bbox(bbox, query_params: http.QueryParams):
    if not kuzzle_client.enabled:
        raise HTTPException("Kuzzle client is not available", status_code=501)

    try:
        params = EventQueryParam(**query_params)
    except ValidationError as e:
        logger.info(f"Validation Error: {e.json()}")
        raise BadRequest(
            detail={"message": e.errors()}
        )

    print(params.outing_types)
    current_outing_lang = params.outing_types

    if params.outing_types:
        lang = params.lang.split(',')[0]
        current_outing_lang = params.outing_types.get(lang)
    print(current_outing_lang)
    bbox_places = kuzzle_client.fetch_event_places(
        bbox=params.bbox,
        collection='events',
        outing_types=current_outing_lang,
        size=params.size
    )

    events_list = [Event(p['_source']) for p in bbox_places]

    return {
        "events": [p.load_place(params.lang, params.verbosity) for p in events_list]
    }
