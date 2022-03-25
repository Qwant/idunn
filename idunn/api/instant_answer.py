import asyncio
import logging
from fastapi import Query
from fastapi.responses import ORJSONResponse, Response
from fastapi.concurrency import run_in_threadpool
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field, validator, HttpUrl
from geopy import Point

from idunn import settings
from idunn.datasources.pages_jaunes import pj_source
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.geocoder.bragi_client import bragi_client
from idunn.geocoder.models import QueryParams
from idunn.geocoder.models.geocodejson import IntentionType
from idunn.places import Place
from idunn.api.places_list import get_places_bbox_impl, PlacesQueryParam
from idunn.utils import maps_urls
from idunn.utils.regions import get_region_lonlat
from idunn.utils.result_filter import ResultFilter
from idunn.instant_answer import normalize
from .constants import PoiSource

from ..utils.place import place_from_id
from ..utils.verbosity import Verbosity
from copy import deepcopy

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
        description="List of relevant places to display on the instant answer. "
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
                "place_id": result.places[0].id if nb_places == 1 else None,
            },
        },
    )
    return ORJSONResponse(
        InstantAnswerResponse(
            data=InstantAnswerData(result=result, query=InstantAnswerQuery(query=query, lang=lang)),
        ).dict()
    )


def get_instant_answer_single_place(
    place_id: str, query: str, lang: str, type: Optional[str] = None
) -> Response:
    try:
        place = place_from_id(place_id, lang, type=type, follow_redirect=True)
    except Exception:
        logger.warning(
            "get_instant_answer: Failed to get place with id '%s'", place_id, exc_info=True
        )
        return no_instant_answer()

    detailed_place = place.load_place(lang=lang)
    result = InstantAnswerResult(
        places=[detailed_place],
        source=place.get_source(),
        intention_bbox=None,
        maps_url=maps_urls.get_place_url(place_id),
        maps_frame_url=maps_urls.get_place_url(place_id, no_ui=True),
    )
    return build_response(result, query=query, lang=lang)


async def get_instant_answer_intention(intention, query: str, lang: str):
    if not intention.filter.bbox:
        return no_instant_answer(query=query, lang=lang)

    category = intention.filter.category

    # For intention results around a point, rerank results by distance
    intention_around_point = None
    intention_place = intention.description.place
    if intention_place and intention_place.properties.geocoding.type == "poi":
        place_coord = intention_place.geometry.get("coordinates")
        if place_coord and len(place_coord) == 2:
            lon, lat = place_coord
            intention_around_point = Point(latitude=lat, longitude=lon)

    places_bbox_response = await get_places_bbox_impl(
        PlacesQueryParam(
            category=[category] if category else [],
            bbox=intention.filter.bbox,
            q=intention.filter.q,
            raw_filter=None,
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
        place_id = places[0].id
        result = InstantAnswerResult(
            places=places,
            source=places_bbox_response.source,
            intention_bbox=intention.filter.bbox,
            maps_url=maps_urls.get_place_url(place_id),
            maps_frame_url=maps_urls.get_place_url(place_id, no_ui=True),
        )
    else:
        result = InstantAnswerResult(
            places=places,
            source=places_bbox_response.source,
            intention_bbox=intention.filter.bbox,
            maps_url=maps_urls.get_places_url(intention.filter),
            maps_frame_url=maps_urls.get_places_url(intention.filter, no_ui=True),
        )

    return build_response(result, query=query, lang=lang)


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
    normalized_query = normalize(q)

    if user_country is not None:
        user_country = user_country.lower()

    if len(normalized_query) > ia_max_query_length:
        return no_instant_answer(query=q, lang=lang, region=user_country)

    extra_geocoder_params = {}

    if user_country and get_region_lonlat(user_country) is not None:
        extra_geocoder_params["lon"], extra_geocoder_params["lat"] = get_region_lonlat(user_country)
        extra_geocoder_params["zoom"] = 6

    if normalized_query == "":
        result = InstantAnswerResult(
            places=[],
            maps_url=maps_urls.get_default_url(),
            maps_frame_url=maps_urls.get_default_url(no_ui=True),
        )
        return build_response(result, query=q, lang=lang)

    intentions = []
    if lang in nlu_allowed_languages:
        try:
            intentions = await nlu_client.get_intentions(
                normalized_query,
                lang,
                extra_geocoder_params,
                allow_types=[
                    IntentionType.BRAND,
                    IntentionType.CATEGORY,
                    IntentionType.POI,
                ],
            )
            if intentions and intentions[0].type in [
                IntentionType.BRAND,
                IntentionType.CATEGORY,
            ]:
                return await get_instant_answer_intention(intentions[0], query=q, lang=lang)
        except NluClientException:
            # No intention could be interpreted from query
            intentions = []

    # Direct geocoding query
    query = QueryParams.build(q=normalized_query, lang=lang, limit=5, **extra_geocoder_params)

    async def fetch_pj_response():
        return await run_in_threadpool(
            pj_source.search_places,
            normalized_query,
            intentions[0].description._place_in_query,
        )

    # Query PJ API and Bragi osm asynchronously as a task which may be cancelled
    # NOTE: As of httpx >=0.18,<=0.22, cancelling these tasks will fill httpx client's internal
    #       connection pool which will lead on bragi not being available
    #       anymore (or a memory leak if the limit is very high).
    #       See https://github.com/encode/httpx/issues/2139
    fetch_pj = asyncio.create_task(fetch_pj_response(), name="ia_fetch_pj")
    fetch_bragi_osm = asyncio.create_task(bragi_client.autocomplete(query), name="ia_fetch_bragi")

    if settings["TRIPADVISOR_ENABLED"]:
        query_tripadvisor = deepcopy(query)
        query_tripadvisor.poi_dataset += ["tripadvisor", "default"]
        bragi_tripadvisor_response = await bragi_client.autocomplete(query_tripadvisor)
        bragi_tripadvisor_features = result_filter.filter_bragi_features(
            normalized_query, bragi_tripadvisor_response["features"]
        )

    # Select datasource instant answer in France
    if (
        intentions
        and intentions[0].filter is not None
        and intentions[0].filter.bbox is not None
        and pj_source.bbox_is_covered(intentions[0].filter.bbox)
    ):
        if settings["TRIPADVISOR_ENABLED"]:
            for bragi_tripadvisor_feature in bragi_tripadvisor_features:
                feature_properties = bragi_tripadvisor_feature["properties"]["geocoding"]
                if (
                    "poi_types" in feature_properties
                    and feature_properties["poi_types"][0]["id"].split(":")[0]
                    in AVAILABLE_CLASS_TYPE_HOTEL_TRIPADVISOR
                ):
                    place_id = feature_properties["id"]
                    return await run_in_threadpool(
                        get_instant_answer_single_place,
                        query=q,
                        place_id=place_id,
                        lang=lang,
                        type="poi_tripadvisor",
                    )

            pj_response = result_filter.filter_places(normalized_query, await fetch_pj)

            if pj_response and settings["PJ_ENABLED"]:
                place_id = pj_response[0].get_id()
                result = InstantAnswerResult(
                    places=[pj_response[0].load_place(lang)],
                    source=pj_response[0].get_source(),
                    maps_url=maps_urls.get_place_url(place_id),
                    maps_frame_url=maps_urls.get_place_url(place_id, no_ui=True),
                )
                return build_response(result, query=q, lang=lang)

    # Call tripadvisor datasource instant answer outside France or
    # without intention location detection
    else:
        if settings["TRIPADVISOR_ENABLED"]:
            bragi_tripadvisor_feature = next(iter(bragi_tripadvisor_features), None)

            if bragi_tripadvisor_feature is not None:
                feature_properties = bragi_tripadvisor_feature["properties"]["geocoding"]
                place_id = feature_properties["id"]
                return await run_in_threadpool(
                    get_instant_answer_single_place,
                    query=q,
                    place_id=place_id,
                    lang=lang,
                )

    return await instant_answer_fallback(fetch_bragi_osm, lang, normalized_query, q, user_country)


async def instant_answer_fallback(fetch_bragi_osm, lang, normalized_query, q, user_country):
    """
    Call OSM datasource as fallback. Return No instant answer if there are no results found
    """
    bragi_osm_response = await fetch_bragi_osm
    bragi_osm_features = result_filter.filter_bragi_features(
        normalized_query, bragi_osm_response["features"]
    )
    if bragi_osm_features:
        place_id = bragi_osm_features[0]["properties"]["geocoding"]["id"]
        return await run_in_threadpool(
            get_instant_answer_single_place, query=q, place_id=place_id, lang=lang
        )
    return no_instant_answer(query=q, lang=lang, region=user_country)
