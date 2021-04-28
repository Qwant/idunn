import logging
from fastapi import Depends, HTTPException

from idunn import settings
from idunn.api.places_list import PlacesBboxResponse
from idunn.geocoder.bragi_client import bragi_client
from idunn.geocoder.models.geocodejson import Intention
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.places import place_from_id
from idunn.utils import result_filter
from idunn.instant_answer import normalize
from .instant_answer import get_instant_answer_intention
from ..geocoder.models import QueryParams, IdunnAutocomplete

logger = logging.getLogger(__name__)

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")


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
    return IdunnAutocomplete()


async def search_intention(intention: Intention, query: str, lang: str) -> IdunnAutocomplete:
    try:
        ia_result = await get_instant_answer_intention(intention, query, lang)
    except HTTPException(status_code=404):
        return IdunnAutocomplete()

    if len(ia_result.places) == 1:
        result = IdunnAutocomplete(place=ia_result.places[0])
    else:
        result = IdunnAutocomplete(
            bbox_places=[
                PlacesBboxResponse(
                    places=ia_result.places,
                    source=ia_result.source,
                    bbox=ia_result.intention_bbox,
                    bbox_extended=False,
                )
            ],
        )

    return result


def search_single_place(place_id: str, lang: str):
    try:
        place = place_from_id(place_id, follow_redirect=True)
    except Exception:
        logger.warning("search: Failed to get place with id '%s'", place_id, exc_info=True)
        return no_search_result()

    detailed_place = place.load_place(lang=lang)
    return IdunnAutocomplete(features=[detailed_place])


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
                return IdunnAutocomplete(intentions=intentions)
        except NluClientException:
            # No intention could be interpreted from query
            pass

    # Direct geocoding query
    bragi_response = await bragi_client.raw_autocomplete(
        {"q": query.q, "lang": query.lang, "limit": 5}
    )

    features = sorted(
        (
            (result_filter.rank_bragi_response(query.q, geocoding), feature)
            for feature in bragi_response["features"]
            for geocoding in [feature["properties"]["geocoding"]]
            if result_filter.check_bragi_response(query.q, geocoding)
        ),
        key=lambda item: -item[0],  # sort by descending rank
    )

    if not features:
        return no_search_result(query=query.q, lang=query.lang)

    return IdunnAutocomplete(features=[features[0][1]])
