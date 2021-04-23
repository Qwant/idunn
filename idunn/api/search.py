import logging
from fastapi import Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import Optional
from pydantic import BaseModel, Field

from idunn import settings
from idunn.api.places_list import PlacesBboxResponse
from idunn.geocoder.bragi_client import bragi_client
from idunn.geocoder.models.geocodejson import Intention
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.places import place_from_id, Place
from idunn.utils import result_filter
from idunn.instant_answer import normalize
from .instant_answer import get_instant_answer_intention
from ..geocoder.models import QueryParams, IdunnAutocomplete

logger = logging.getLogger(__name__)

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")


class SearchResult(BaseModel):
    """Exactly one of the fields `places` or `place` are defined."""

    bbox_places: Optional[PlacesBboxResponse] = Field(
        None, description="A list of places as results."
    )
    place: Optional[Place] = Field(None, description="A list of places as results.")


def no_search_result(query=None, lang=None):
    if query is not None:
        logger.info(
            "search: no result",
            extra={
                "request": {
                    "query": query,
                    "lang": lang,
                }
            },
        )
    return SearchResult()


async def search_intention(intention: Intention, query: str, lang: str) -> SearchResult:
    try:
        ia_result = await get_instant_answer_intention(intention, query, lang)
    except HTTPException(status_code=404):
        return SearchResult()

    if len(ia_result.places) == 1:
        result = SearchResult(place=ia_result.places[0])
    else:
        result = SearchResult(
            bbox_places=PlacesBboxResponse(
                places=ia_result.places,
                source=ia_result.source,
                bbox=ia_result.intention_bbox,
                bbox_extended=False,
            ),
        )

    return result


def search_single_place(place_id: str, lang: str):
    try:
        place = place_from_id(place_id, follow_redirect=True)
    except Exception:
        logger.warning("search: Failed to get place with id '%s'", place_id, exc_info=True)
        return no_search_result()

    detailed_place = place.load_place(lang=lang)
    return SearchResult(place=detailed_place)


async def search(query: QueryParams = Depends(QueryParams)) -> IdunnAutocomplete:
    """
    Perform a query which is intended to display a relevant result directly (as
    opposed to `autocomplete` which gives a list of plausible results).

    Similarly to `instant_answer`, the result will need some quality checks.
    """
    query.q = normalize(query.q)

    if query.lang in nlu_allowed_languages:
        try:
            intentions = await nlu_client.get_intentions(text=query.q, lang=query.lang)
            if intentions:
                return await search_intention(intentions[0], query=query.q, lang=query.lang)
        except NluClientException:
            # No intention could be interpreted from query
            pass

    # Direct geocoding query
    bragi_response = await bragi_client.raw_autocomplete(
        {"q": query.q, "lang": query.lang, "limit": 5}
    )
    geocodings = (feature["properties"]["geocoding"] for feature in bragi_response["features"])
    geocodings = sorted(
        (
            (result_filter.rank_bragi_response(query.q, feature), feature)
            for feature in geocodings
            if result_filter.check_bragi_response(query.q, feature)
        ),
        key=lambda item: -item[0],  # sort by descending rank
    )

    if not geocodings:
        return no_search_result(query=query.q, lang=query.lang)

    place_id = geocodings[0][1]["id"]
    result = await run_in_threadpool(search_single_place, place_id=place_id, lang=query.lang)
    return result
