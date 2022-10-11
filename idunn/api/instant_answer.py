import asyncio
import logging
from typing import Optional, List, Tuple, Union

from fastapi import Query
from fastapi.responses import ORJSONResponse, Response
from geopy import Point
from pydantic import BaseModel, Field, validator, HttpUrl

from idunn import settings
from idunn.api.places_list import get_places_bbox_impl, PlacesQueryParam
from idunn.datasources.pages_jaunes import pj_source
from idunn.geocoder.models import QueryParams
from idunn.geocoder.models.geocodejson import IntentionType
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.places import Place
from idunn.utils import maps_urls
from idunn.utils.regions import get_region_lonlat
from idunn.utils.result_filter import ResultFilter
from .constants import PoiSource
from ..datasources import Datasource
from ..datasources.osm import Osm
from ..datasources.tripadvisor import Tripadvisor, ta
from ..instant_answer.normalization import normalize_instant_answer_param
from ..utils.verbosity import Verbosity

logger = logging.getLogger(__name__)
result_filter = ResultFilter()

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")
ia_max_query_length = int(settings["IA_MAX_QUERY_LENGTH"])
AVAILABLE_CLASS_TYPE_TRIPADVISOR = [
    "class_hotel",
    "class_lodging",
    "class_restaurant",
    "class_leisure",
]

AVAILABLE_CLASS_TYPE_HOTEL_TRIPADVISOR = [
    "class_hotel",
    "class_lodging",
]


class InstantAnswerResult(BaseModel):
    places: List[Place] = Field(
        description="List of relevant places to display on the instant answer."
        "When no place is returned, display the default instant answer"
        "At most 1 place is returned if no broad intention has been detected."
    )
    source: Optional[PoiSource] = Field(
        description=(
            "Data source for the returned place, or data provider for the list of results. This "
            "field is not provided when the instant answer relates to an administrative area or an "
            "address."
        )
    )
    intention_bbox: Optional[Tuple[float, float, float, float]] = Field(
        description=(
            "Bounding box where the results have been searched for, based on the detected "
            "intention. Not provided when no detected intention was used to fetch the results."
        ),
        example=(2.32, 48.85, 2.367, 48.866),
    )
    maps_url: HttpUrl = Field(
        description="Direct URL to the result(s) on Qwant Maps.",
    )
    maps_frame_url: HttpUrl = Field(
        description="URL to the map displaying the results on Qwant Maps, with no user interface. "
        "This URL can be used to display an `<iframe>`."
    )

    @validator("intention_bbox")
    def round_bbox_values(cls, v):
        if v is None:
            return v
        return tuple(round(x, 6) for x in v)


class InstantAnswerQuery(BaseModel):
    query: str
    lang: str


class InstantAnswerData(BaseModel):
    query: InstantAnswerQuery
    result: InstantAnswerResult


class InstantAnswerResponse(BaseModel):
    status: str = "success"
    data: InstantAnswerData


def no_instant_answer(query=None, lang=None, region=None):
    if query is not None:
        logger.info(
            "get_instant_answer: no answer",
            extra={
                "request": {
                    "query": query,
                    "lang": lang,
                    "region": region,
                }
            },
        )
    return Response(status_code=204)


def build_response(result: InstantAnswerResult, query: str, lang: str):
    nb_places = len(result.places)
    logger.info(
        "get_instant_answer: OK",
        extra={
            "request": {
                "query": query,
                "lang": lang,
            },
            "response": {
                "nb_places": nb_places,
                "source": result.source,
                "place_id": result.places[0].id if nb_places == 1 else None,
            },
        },
    )
    return ORJSONResponse(
        InstantAnswerResponse(
            data=InstantAnswerData(result=result, query=InstantAnswerQuery(query=query, lang=lang)),
        ).dict()
    )


async def get_instant_answer_intention(intention, query: str, lang: str):
    # if there is not brand or category intention with an associated place
    if not intention.filter.bbox:
        return no_instant_answer(query=query, lang=lang)

    category = intention.filter.category

    # For intention results around a point, rerank results by distance
    intention_around_point = None
    intention_place = intention.description.place
    if intention_place and intention_place["properties"]["geocoding"]["type"] == "poi":
        place_coord = intention_place.geometry.get("coordinates")
        if place_coord and len(place_coord) == 2:
            lon, lat = place_coord
            intention_around_point = Point(latitude=lat, longitude=lon)

    places_bbox_response = await get_places_bbox_impl(
        PlacesQueryParam(
            category=[category] if category else [],
            bbox=intention.filter.bbox,
            place=intention.description.place["properties"]["geocoding"],
            q=intention.filter.q,
            source=None,
            size=10,
            lang=lang,
            extend_bbox=True,
            verbosity=Verbosity.default_list(),
        ),
        sort_by_distance=intention_around_point,
    )

    places = places_bbox_response.places
    if len(places) == 0:
        return no_instant_answer(query=query, lang=lang)

    if len(places) == 1:
        return build_single_ia_answer(lang, query, places[0], intention.filter.bbox)

    result = InstantAnswerResult(
        places=places,
        source=places_bbox_response.source,
        intention_bbox=intention.filter.bbox,
        maps_url=maps_urls.get_places_url(intention.filter),
        maps_frame_url=maps_urls.get_places_url(intention.filter, no_ui=True),
    )

    return build_response(result, query=query, lang=lang)


def get_single_ia_datasource_priority_france(
    fetch_bragi_tripadvisor, fetch_pj, fetch_bragi_osm
) -> List[Union[Datasource, any]]:
    return [
        (ta, fetch_bragi_tripadvisor),
        (pj_source, fetch_pj),
        (Osm(is_wiki_filter=False), fetch_bragi_osm),
    ]


def get_single_ia_datasource_priority_world(
    fetch_bragi_tripadvisor, fetch_bragi_osm
) -> List[Union[Datasource, any]]:
    return [
        (Osm(is_wiki_filter=True), fetch_bragi_osm),
        (ta, fetch_bragi_tripadvisor),
        (Osm(is_wiki_filter=False), fetch_bragi_osm),
    ]


async def get_instant_answer(
    q: str = Query(..., title="Query string"),
    lang: str = Query("en", title="Language"),
    user_country: Optional[str] = Query(None, title="Region where the user is located"),
):
    """
    Perform a query with result intended to be displayed as an instant answer
    on *qwant.com*.

    This should not be confused with "Get Places Bbox" as this endpoint will
    run more restrictive checks on its results.
    """
    normalized_query, user_country = normalize_instant_answer_param(q, user_country)

    if len(normalized_query) > ia_max_query_length:
        return no_instant_answer(query=q, lang=lang, region=user_country)

    if normalized_query == "":
        result = InstantAnswerResult(
            places=[],
            maps_url=maps_urls.get_default_url(),
            maps_frame_url=maps_urls.get_default_url(no_ui=True),
        )
        return build_response(result, query=q, lang=lang)

    extra_geocoder_params = {}

    if user_country and get_region_lonlat(user_country) is not None:
        extra_geocoder_params["lon"], extra_geocoder_params["lat"] = get_region_lonlat(user_country)
        extra_geocoder_params["zoom"] = 6

    intention = None
    if lang in nlu_allowed_languages:
        try:
            intention = await nlu_client.get_intention(
                normalized_query,
                lang,
                extra_geocoder_params,
                allow_types=[IntentionType.BRAND, IntentionType.CATEGORY, IntentionType.POI],
            )
            if intention and intention.type in [IntentionType.BRAND, IntentionType.CATEGORY]:
                return await get_instant_answer_intention(intention, query=q, lang=lang)
        except NluClientException:
            # No intention could be interpreted from query
            intention = None

    # Direct geocoding query
    query = QueryParams.build(q=normalized_query, lang=lang, limit=1, **extra_geocoder_params)

    try:
        is_france_query = pj_source.bbox_is_covered(intention.filter.bbox)
    except Exception:
        is_france_query = False

    # Query PJ API and Bragi osm asynchronously as a task which may be cancelled
    # NOTE: As of httpx >=0.18,<=0.22, cancelling these tasks will fill httpx client's internal
    #       connection pool which will lead on bragi not being available
    #       anymore (or a memory leak if the limit is very high).
    #       See https://github.com/encode/httpx/issues/2139
    fetch_bragi_osm = asyncio.create_task(await Osm.fetch_search(query), name="ia_fetch_bragi")
    fetch_bragi_tripadvisor = asyncio.create_task(
        await Tripadvisor.fetch_search(query, is_france_query=is_france_query),
        name="fetch_ta_bragi",
    )
    if is_france_query:
        fetch_pj = asyncio.create_task(
            await pj_source.fetch_search(normalized_query, intention=intention),
            name="ia_fetch_pj",
        )
        datasource_priority_list = get_single_ia_datasource_priority_france(
            fetch_bragi_tripadvisor, fetch_pj, fetch_bragi_osm
        )
    else:
        datasource_priority_list = get_single_ia_datasource_priority_world(
            fetch_bragi_tripadvisor, fetch_bragi_osm
        )

    for (datasource, task) in datasource_priority_list:
        datasource_response = await task
        result_place = datasource.filter_search_result(datasource_response, lang, normalized_query)
        if result_place:
            return build_single_ia_answer(lang, q, result_place)

    return no_instant_answer(query=q, lang=lang, region=user_country)


def build_single_ia_answer(lang, q, result_place, intention_bbox=None):
    result = InstantAnswerResult(
        places=[result_place],
        source=result_place.meta.source,
        intention_bbox=intention_bbox,
        maps_url=maps_urls.get_place_url(result_place.id),
        maps_frame_url=maps_urls.get_place_url(result_place.id, no_ui=True),
    )
    return build_response(result, query=q, lang=lang)
