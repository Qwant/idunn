import asyncio
import logging
from typing import Optional

from fastapi import Body, Depends
from fastapi.responses import ORJSONResponse
from ..geocoder.bragi_client import bragi_client
from ..geocoder.models.geocodejson import Intention
from ..geocoder.nlu_client import nlu_client, NluClientException
from ..geocoder.models import QueryParams, ExtraParams, IdunnAutocomplete

from idunn import settings
from idunn.utils.result_filter import ResultFilter

logger = logging.getLogger(__name__)
result_filter = ResultFilter()

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")
autocomplete_nlu_filter_intentions = settings["AUTOCOMPLETE_NLU_FILTER_INTENTIONS"]


def filter_wrong_brand_intention(intention: Intention, bragi_response, limit):
    if not intention.description.query or intention.description.place:
        return intention

    # Detected intention is a full-text query only (brand).
    # A generic brand query will typically match dozens of POIs.
    # To avoid false positives, let's ignore the intention if matching
    # results among geocoded features seem to be too rare.
    expected_matches = limit / 2
    matches = len(
        result_filter.filter_bragi_features(
            intention.description.query,
            [
                feat
                for feat in bragi_response["features"]
                if feat.get("properties", {}).get("geocoding", {}).get("type") == "poi"
            ],
        )
    )

    if matches > expected_matches:
        return intention

    logging.info(
        "Ignored intention which doesn't match enough geocoding results `%s`",
        intention.description.query,
        extra={
            "intention": intention.dict(),
            "bragi_response": [
                {
                    "id": feat.get("properties", {}).get("geocoding", {}).get("id"),
                    "label": feat.get("properties", {}).get("geocoding", {}).get("label"),
                }
                for feat in bragi_response["features"]
            ],
            "limit": limit,
        },
    )
    return None


async def get_autocomplete(
    query: QueryParams = Depends(QueryParams),
    extra: ExtraParams = Body(ExtraParams()),
) -> IdunnAutocomplete:
    """
    Get a list of suggested places or intentions from a potentially incomplete
    query.
    """

    async def get_intention() -> Optional[Intention]:
        if query.lang not in nlu_allowed_languages or not query.nlu:
            return None

        try:
            return await nlu_client.get_intention(text=query.q, lang=query.lang)
        except NluClientException as exp:
            logger.info("Ignored NLU for '%s': %s", query.q, exp.reason(), extra=exp.extra)
            return None

    autocomplete_response, intention = await asyncio.gather(
        bragi_client.autocomplete(query, extra), get_intention()
    )
    if intention is not None and query.nlu:
        if autocomplete_nlu_filter_intentions:
            intention = filter_wrong_brand_intention(intention, autocomplete_response, query.limit)
        autocomplete_response["intention"] = intention
    autocomplete_response["geocoding"]["query"] = query.q
    return IdunnAutocomplete(**autocomplete_response)


async def get_autocomplete_response(autocomplete: IdunnAutocomplete = Depends(get_autocomplete)):
    return ORJSONResponse(autocomplete.dict(exclude_unset=True))
