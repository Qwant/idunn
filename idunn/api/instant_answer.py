import logging
from fastapi import HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from typing import Optional, List, Any, Tuple
from pydantic import BaseModel, Field, validator, HttpUrl

from idunn import settings
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.geocoder.bragi_client import bragi_client
from idunn.places import place_from_id, Place
from idunn.api.places_list import get_places_bbox
from idunn.utils import maps_urls
from .constants import PoiSource

logger = logging.getLogger(__name__)

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")


class InstantAnswerResult(BaseModel):
    places: List[Place] = Field(
        description="List of relevant places to display on the instant answer. "
        "At most 1 place is returned if no broad intention has been detected."
    )
    source: Optional[PoiSource] = Field(
        description="Data source for the returned place, or data provider for the list of results. "
        "This field is not provided when the instant answer relates to an admnistrative area or an address."
    )
    intention_bbox: Optional[Tuple[float, float, float, float]] = Field(
        description="Bounding box where the results have been searched for, based on the detected intention."
        "Not provided when no detected intention was used to fetch the results.",
        example=(2.32, 48.85, 2.367, 48.866),
    )
    maps_url: HttpUrl = Field(description="Direct URL to the result(s) on Qwant Maps.",)
    maps_frame_url: HttpUrl = Field(
        description="URL to the map displaying the results on Qwant Maps, with no user interface. "
        "This URL can be used to display an `<iframe>`."
    )

    @validator("intention_bbox")
    @classmethod
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


def build_response(result: InstantAnswerResult, query: str, lang: str):
    return InstantAnswerResponse(
        data=InstantAnswerData(result=result, query=InstantAnswerQuery(query=query, lang=lang))
    )


def get_instant_answer_single_place(place_id: str, lang: str):
    try:
        place = place_from_id(place_id, follow_redirect=True)
    except:
        logger.warning("Failed to get place for instant answer", exc_info=True)
        raise HTTPException(status_code=404)

    detailed_place = place.load_place(lang=lang)
    return InstantAnswerResult(
        places=[detailed_place],
        source=place.get_source(),
        intention_bbox=None,
        maps_url=f"https://www.qwant.com/maps/place/{place_id}",
        maps_frame_url=f"https://www.qwant.com/maps/place/{place_id}?no_ui=1",
    )


async def get_instant_answer(
    q: str = Query(..., title="Query string"), lang: str = Query("en", title="Language")
):
    """
    Perform a query with result intended to be displayed as an instant answer
    on *qwant.com*.

    This should not be confused with "Get Places Bbox" as this endpoint will
    run more restrictive checks on its results.
    """
    q = q.strip()
    if lang in nlu_allowed_languages:
        try:
            intentions = await nlu_client.get_intentions(text=q, lang=lang)
        except NluClientException:
            intentions = []
    else:
        intentions = []

    if not intentions:
        bragi_response = await bragi_client.raw_autocomplete({"q": q, "lang": lang, "limit": 1})
        if len(bragi_response["features"]) > 0:
            place_geocoding = bragi_response["features"][0]["properties"]["geocoding"]
            place_id = place_geocoding["id"]
            place_name = place_geocoding["name"]
            # TODO: use smarter condition to allow inexact matches
            if place_name.lower() == q.lower():
                result = await run_in_threadpool(
                    get_instant_answer_single_place, place_id=place_id, lang=lang
                )
                return build_response(result, query=q, lang=lang)
        raise HTTPException(404)

    intention = intentions[0]
    if not intention.filter.bbox:
        raise HTTPException(404)

    category = intention.filter.category

    places_bbox_response = await get_places_bbox(
        category=[category] if category else [],
        bbox=intention.filter.bbox,
        q=intention.filter.q,
        raw_filter=None,
        source=None,
        size=10,
        lang=lang,
        extend_bbox=True,
    )

    places = places_bbox_response.places
    if len(places) == 0:
        raise HTTPException(404)

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

    return build_response(result, query=q, lang=lang)
