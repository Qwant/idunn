import logging
from typing import List, Optional, Any, Tuple

from fastapi import HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from geopy.distance import distance
from geopy.point import Point
from pydantic import BaseModel, ValidationError, validator, root_validator, Field
from shapely.affinity import scale
from shapely.geometry import MultiPoint, box

from idunn import settings
from idunn.datasources.pages_jaunes import pj_source, PagesJaunes
from .constants import PoiSource, ALL_POI_SOURCES
from ..datasources import Datasource
from ..datasources.osm import Osm
from ..datasources.tripadvisor import Tripadvisor
from ..utils.category import Category
from ..utils.verbosity import Verbosity

logger = logging.getLogger(__name__)

MAX_WIDTH = 1.0  # max bbox longitude in degrees
MAX_HEIGHT = 1.0  # max bbox latitude in degrees
EXTENDED_BBOX_MAX_SIZE = float(
    settings["LIST_PLACES_EXTENDED_BBOX_MAX_SIZE"]
)  # max bbox width and height after second extended query
TRIPADVISOR_CATEGORIES_COVERED = ["hotel", "leisure", "attraction", "restaurant"]


class CommonQueryParam(BaseModel):
    bbox: Tuple[float, float, float, float] = None
    size: int = None
    lang: str = None
    verbosity: Verbosity = Field(...)

    @validator("lang", pre=True, always=True)
    def valid_lang(cls, v):
        if v is None:
            v = settings["DEFAULT_LANGUAGE"]
        return v.lower()

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
    category: List[Category] = []
    raw_filter: Optional[List[str]]
    source: Optional[str]
    q: Optional[str]
    extend_bbox: bool = False

    def __init__(self, **data: Any):
        try:
            super().__init__(**data)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.errors()) from e

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


class PlacesBboxResponse(BaseModel):
    places: List[Any]
    source: PoiSource
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        description=(
            "Minimal bbox containing all results. `null` if no result is found. May be larger than "
            "or outside of the original bbox passed in the query if `?extend_bbox=true` was set."
        ),
        example=(2.32, 48.85, 2.367, 48.866),
    )
    bbox_extended: bool = Field(
        description=(
            "`true` if `?extend_bbox=true` was set and search has been executed on an extended "
            "bbox, after no result was found in the original bbox passed in the query."
        )
    )

    @validator("bbox")
    def round_bbox_values(cls, v):
        if v is None:
            return v
        return tuple(round(x, 6) for x in v)


# TODO: using `Depends` could probably help since `locals()` seems quite dirty
# pylint: disable = unused-argument
async def get_places_bbox(
    bbox: str = Query(
        ...,
        title="Bounding box",
        description="Format: left_lon,bottom_lat,right_lon,top_lat",
        example="-4.56,48.35,-4.42,48.46",
    ),
    category: List[Category] = Query([]),
    raw_filter: Optional[List[str]] = Query(None),
    source: Optional[str] = Query(None),
    q: Optional[str] = Query(None, title="Query", description="Full text query"),
    size: Optional[int] = Query(None),
    lang: Optional[str] = Query(None),
    verbosity: Verbosity = Verbosity.default_list(),
    extend_bbox: bool = Query(False),
) -> PlacesBboxResponse:
    """Get all places in a bounding box."""
    params = PlacesQueryParam(**locals())
    return await get_places_bbox_impl(params)


async def get_places_bbox_impl(
    params: PlacesQueryParam,
    sort_by_distance: Optional[Point] = None,
) -> PlacesBboxResponse:
    if params.source is None:
        if (
            params.q or (params.category and all(c.pj_what() for c in params.category))
        ) and pj_source.bbox_is_covered(params.bbox):
            params.source = PoiSource.PAGESJAUNES
        elif any(cat in params.category for cat in TRIPADVISOR_CATEGORIES_COVERED):
            params.source = PoiSource.TRIPADVISOR
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

    if sort_by_distance:
        places_list.sort(key=lambda p: distance(sort_by_distance, p.get_point()))

    result_places = await run_in_threadpool(
        lambda: [p.load_place(params.lang, params.verbosity) for p in places_list]
    )

    return PlacesBboxResponse(
        places=result_places,
        source=params.source,
        bbox=results_bbox,
        bbox_extended=bbox_extended,
    )


async def _fetch_places_list(params: PlacesQueryParam):
    datasource = DatasourceFactory().get_datasource(params.source)
    return await datasource.get_places_bbox(params)


class DatasourceFactory:
    def get_datasource(self, source_type: PoiSource) -> Datasource:
        """Get the matching datasource to fetch POIs"""
        if source_type == PoiSource.TRIPADVISOR:
            return Tripadvisor()
        if source_type == PoiSource.PAGESJAUNES:
            return PagesJaunes()
        if source_type == PoiSource.OSM:
            return Osm()
        logger.error("%s is not a valid source type, OSM source is used as fallback", source_type)
        return Osm()
