import os
import logging

from fastapi import HTTPException, Query

from idunn import settings
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.utils.settings import _load_yaml_file
from idunn.utils.index_names import INDICES
from idunn.places import POI
from idunn.api.utils import (
    fetch_bbox_places,
    DEFAULT_VERBOSITY_LIST,
    ALL_VERBOSITY_LEVELS,
)
from idunn.places.event import Event
from .pages_jaunes import pj_source
from .constants import SOURCE_OSM, SOURCE_PAGESJAUNES
from .kuzzle import kuzzle_client

from pydantic import BaseModel, ValidationError, validator
from typing import List, Optional, Any, Tuple


logger = logging.getLogger(__name__)

MAX_WIDTH = 1.0  # max bbox longitude in degrees
MAX_HEIGHT = 1.0  # max bbox latitude in degrees

ALL_SOURCES = [SOURCE_OSM, SOURCE_PAGESJAUNES]


def get_categories():
    categories_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml"
    )
    return _load_yaml_file(categories_path)["categories"]


def get_outing_types():
    outing_types_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml"
    )
    return _load_yaml_file(outing_types_path)["outing_types"]


ALL_CATEGORIES = get_categories()
ALL_OUTING_CATEGORIES = get_outing_types()


class CommonQueryParam(BaseModel):
    bbox: Tuple[float, float, float, float] = None
    size: int = None
    lang: str = None
    verbosity: str = None

    @validator("lang", pre=True, always=True)
    def valid_lang(cls, v):
        if v is None:
            v = settings["DEFAULT_LANGUAGE"]
        return v.lower()

    @validator("verbosity", pre=True, always=True)
    def valid_verbosity(cls, v):
        if v is None:
            v = DEFAULT_VERBOSITY_LIST
        if v not in ALL_VERBOSITY_LEVELS:
            raise ValueError(
                f"the verbosity: '{v}' does not belong to possible verbosity levels: {VERBOSITY_LEVELS}"
            )
        return v

    @validator("size", pre=True, always=True)
    def max_size(cls, v):
        max_size = settings["LIST_PLACES_MAX_SIZE"]
        sizes = [v, max_size]
        return min(int(i) for i in sizes if i is not None)

    @validator("bbox", pre=True, always=True)
    def valid_bbox(cls, v):
        v = v.split(",")
        if len(v) != 4:
            raise ValueError("bbox should contain 4 numbers")
        left, bot, right, top = float(v[0]), float(v[1]), float(v[2]), float(v[3])
        if left > right or bot > top:
            raise ValueError("bbox dimensions are invalid")
        if (right - left > MAX_WIDTH) or (top - bot > MAX_HEIGHT):
            raise ValueError("bbox is too large")
        return (left, bot, right, top)


class PlacesQueryParam(CommonQueryParam):
    category: List[Any]
    raw_filter: Optional[List[str]]
    source: Optional[str]
    q: Optional[str]

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.raw_filter and not self.category and not self.q:
            raise HTTPException(
                status_code=400,
                detail="One of 'category', 'raw_filter' or 'q' parameter is required",
            )

    @validator("source", pre=True, always=True)
    def valid_source(cls, v):
        if not v:
            return None
        if v not in ALL_SOURCES:
            raise ValueError(f"unknown source: '{v}'")
        return v

    @validator("raw_filter", pre=True, always=True)
    def valid_raw_filter(cls, v):
        if not v:
            return []
        for x in v:
            if "," not in x:
                raise ValueError(f"raw_filter '{x}' is invalid from '{v}'")
        return v

    @validator("category", pre=True, always=True)
    def valid_category(cls, v):
        ret = []
        if not v:
            return ret
        for x in v:
            if x not in ALL_CATEGORIES:
                raise ValueError(
                    f"Category '{x}' is invalid since it does not belong to the set of possible categories: {list(ALL_CATEGORIES.keys())}"
                )
            ret.append(ALL_CATEGORIES.get(x))
        return ret


class EventQueryParam(CommonQueryParam):
    category: Optional[str]

    @validator("category", pre=True, always=True)
    def valid_categories(cls, v):
        if v is None:
            return None
        if v not in ALL_OUTING_CATEGORIES:
            raise ValueError(
                f"outing_types '{v}' is invalid since it does not belong to set of possible outings type: {list(ALL_OUTING_CATEGORIES.keys())}"
            )
        else:
            v = ALL_OUTING_CATEGORIES.get(v, {})
        return v


def get_raw_params(bbox, category, raw_filter, source, q, size, lang, verbosity):
    raw_params = {
        "bbox": bbox,
        "category": category,
        "raw_filter": raw_filter,
        "source": source,
        "q": q,
        "size": size,
        "lang": lang,
        "verbosity": verbosity,
    }
    if raw_params.get("raw_filter") and raw_params.get("category"):
        raise HTTPException(
            status_code=400,
            detail="Both 'raw_filter' and 'category' parameters cannot be provided together",
        )
    return raw_params


def get_places_bbox(
    bbox: Any,
    category: Optional[List[str]] = Query(None),
    raw_filter: Optional[List[str]] = Query(None),
    source: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    size: Optional[int] = Query(None),
    lang: Optional[str] = Query(None),
    verbosity: Optional[str] = Query(None),
):
    es = get_elasticsearch()
    raw_params = get_raw_params(bbox, category, raw_filter, source, q, size, lang, verbosity)
    try:
        params = PlacesQueryParam(**raw_params)
    except ValidationError as e:
        logger.info(f"Validation Error: {e.json()}")
        raise HTTPException(status_code=400, detail=e.errors())

    source = params.source
    if source is None:
        if params.q:
            # PJ is currently the only source that accepts arbitrary queries
            source = SOURCE_PAGESJAUNES
        elif (
            params.category
            and all(c.get("pj_filters") for c in params.category)
            and pj_source.bbox_is_covered(params.bbox)
        ):
            source = SOURCE_PAGESJAUNES
        else:
            source = SOURCE_OSM

    if source == SOURCE_PAGESJAUNES:
        all_categories = [pj_category for c in params.category for pj_category in c["pj_filters"]]
        places_list = pj_source.get_places_bbox(
            all_categories, params.bbox, size=params.size, query=params.q
        )
    else:
        # Default source (OSM)
        if params.raw_filter:
            raw_filters = params.raw_filter
        else:
            raw_filters = [f for c in params.category for f in c["raw_filters"]]

        bbox_places = fetch_bbox_places(
            es, INDICES, raw_filters=raw_filters, bbox=params.bbox, max_size=params.size
        )
        places_list = [POI(p["_source"]) for p in bbox_places]

    return {
        "places": [p.load_place(params.lang, params.verbosity) for p in places_list],
        "source": source,
    }


def get_events_bbox(
    bbox: str,
    category: Optional[str] = Query(None),
    size: int = Query(None),
    lang: Optional[str] = Query(None),
    verbosity: Optional[str] = Query(None),
):
    if not kuzzle_client.enabled:
        raise HTTPException(status_code=501, detail="Kuzzle client is not available")

    try:
        params = EventQueryParam(
            **{
                "category": category,
                "bbox": bbox,
                "size": size,
                "lang": lang,
                "verbosity": verbosity,
            }
        )
    except ValidationError as e:
        logger.info(f"Validation Error: {e.json()}")
        raise HTTPException(status_code=400, detail=e.errors())

    current_outing_lang = params.category

    if params.category:
        current_outing_lang = params.category.get("fr")

    bbox_places = kuzzle_client.fetch_event_places(
        bbox=params.bbox, collection="events", category=current_outing_lang, size=params.size
    )

    events_list = [Event(p["_source"]) for p in bbox_places]

    return {"events": [p.load_place(params.lang, params.verbosity) for p in events_list]}
