import os
import logging

from shapely.geometry import MultiPoint, box
from shapely.affinity import scale
from fastapi import HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from idunn import settings
from idunn.utils.settings import _load_yaml_file
from idunn.places import Place, POI, BragiPOI
from idunn.api.utils import (
    fetch_es_pois,
    DEFAULT_VERBOSITY_LIST,
    ALL_VERBOSITY_LEVELS,
)
from idunn.places.event import Event
from idunn.geocoder.bragi_client import bragi_client
from idunn.datasources.pages_jaunes import pj_source
from idunn.datasources.kuzzle import kuzzle_client
from .constants import PoiSource, ALL_POI_SOURCES

from pydantic import BaseModel, ValidationError, validator, root_validator, Field
from typing import List, Optional, Any, Tuple


logger = logging.getLogger(__name__)

MAX_WIDTH = 1.0  # max bbox longitude in degrees
MAX_HEIGHT = 1.0  # max bbox latitude in degrees
EXTENDED_BBOX_MAX_SIZE = float(
    settings["LIST_PLACES_EXTENDED_BBOX_MAX_SIZE"]
)  # max bbox width and height after second extended query


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
                f"the verbosity: '{v}' does not belong to possible verbosity levels: {ALL_VERBOSITY_LEVELS}"
            )
        return v

    @validator("size", pre=True, always=True)
    def max_size(cls, v):
        max_size = settings["LIST_PLACES_MAX_SIZE"]
        sizes = [v, max_size]
        return min(int(i) for i in sizes if i is not None)

    @validator("bbox", pre=True, always=True)
    def valid_bbox(cls, v):
        if isinstance(v, str):
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
    extend_bbox: bool = False

    def __init__(self, **data: Any):
        try:
            super().__init__(**data)
        except ValidationError as e:
            raise HTTPException(
                status_code=400, detail=e.errors(),
            )

    @validator("source", pre=True, always=True)
    def valid_source(cls, v):
        if not v:
            return None
        if v not in ALL_POI_SOURCES:
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

    @root_validator(skip_on_failure=True)
    def categories_or_raw_filters(cls, values):
        if values.get("raw_filter") and values.get("category"):
            raise HTTPException(
                status_code=400,
                detail="Both 'raw_filter' and 'category' parameters cannot be provided together",
            )
        return values

    @root_validator(skip_on_failure=True)
    def any_query_present(cls, values):
        if not any((values.get("raw_filter"), values.get("category"), values.get("q"))):
            raise HTTPException(
                status_code=400,
                detail="One of 'category', 'raw_filter' or 'q' parameter is required",
            )
        return values


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


class PlacesBboxResponse(BaseModel):
    places: List[Any]
    source: PoiSource
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        description="Minimal bbox containing all results. `null` if no result is found. May be larger than or outside of the original bbox passed in the query if `?extend_bbox=true` was set.",
        example=(2.32, 48.85, 2.367, 48.866),
    )
    bbox_extended: bool = Field(
        description="`true` if `?extend_bbox=true` was set and search has been executed on an extended bbox, after no result was found in the original bbox passed in the query."
    )

    @validator("bbox")
    def round_bbox_values(cls, v):
        if v is None:
            return v
        return tuple(round(x, 6) for x in v)


async def get_places_bbox(
    bbox: str = Query(
        ...,
        title="Bounding box to search",
        description="Format: left_lon,bottom_lat,right_lon,top_lat",
        example="-4.56,48.35,-4.42,48.46",
    ),
    category: Optional[List[str]] = Query(None),
    raw_filter: Optional[List[str]] = Query(None),
    source: Optional[str] = Query(None),
    q: Optional[str] = Query(None, title="Query", description="Full text query"),
    size: Optional[int] = Query(None),
    lang: Optional[str] = Query(None),
    verbosity: Optional[str] = Query(None),
    extend_bbox: bool = Query(False),
) -> PlacesBboxResponse:
    params = PlacesQueryParam(**locals())
    source = params.source
    if source is None:
        if (
            params.q or (params.category and all(c.get("pj_filters") for c in params.category))
        ) and pj_source.bbox_is_covered(params.bbox):
            params.source = PoiSource.PAGESJAUNES
        else:
            params.source = PoiSource.OSM

    places_list = await _fetch_places_list(params)
    bbox_extended = False

    if params.extend_bbox and len(places_list) == 0:
        original_bbox = params.bbox
        original_bbox_width = original_bbox[2] - original_bbox[0]
        original_bbox_height = original_bbox[3] - original_bbox[1]
        original_bbox_size = max(original_bbox_height, original_bbox_width)
        if original_bbox_size < EXTENDED_BBOX_MAX_SIZE:
            # Compute extended bbox and fetch results a second time
            scale_factor = EXTENDED_BBOX_MAX_SIZE / original_bbox_size
            new_box = scale(box(*original_bbox), xfact=scale_factor, yfact=scale_factor)
            params.bbox = new_box.bounds
            bbox_extended = True
            places_list = await _fetch_places_list(params)

    if len(places_list) == 0:
        results_bbox = None
    else:
        points = MultiPoint([(p.get_coord()["lon"], p.get_coord()["lat"]) for p in places_list])
        results_bbox = points.bounds

    result_places = await run_in_threadpool(
        lambda: [p.load_place(params.lang, params.verbosity) for p in places_list]
    )

    return PlacesBboxResponse(
        places=result_places, source=params.source, bbox=results_bbox, bbox_extended=bbox_extended,
    )


async def _fetch_places_list(params: PlacesQueryParam):
    if params.source == PoiSource.PAGESJAUNES:
        return await run_in_threadpool(
            pj_source.get_places_bbox,
            params.category,
            params.bbox,
            size=params.size,
            query=params.q,
        )
    if params.q:
        # Default source (OSM) with query
        bragi_response = await bragi_client.pois_query_in_bbox(
            query=params.q, bbox=params.bbox, lang=params.lang, limit=params.size
        )
        return [BragiPOI(f) for f in bragi_response.get("features", [])]

    # Default source (OSM) with category or class/subclass filters
    if params.raw_filter:
        raw_filters = params.raw_filter
    else:
        raw_filters = [f for c in params.category for f in c["raw_filters"]]

    bbox_places = await run_in_threadpool(
        fetch_es_pois, raw_filters=raw_filters, bbox=params.bbox, max_size=params.size,
    )
    return [POI(p["_source"]) for p in bbox_places]


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
