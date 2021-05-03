import logging
from fastapi import Body, Depends

from idunn import settings
from idunn.geocoder.bragi_client import bragi_client
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.utils import result_filter
from idunn.instant_answer import normalize
from ..geocoder.models import ExtraParams, QueryParams, IdunnAutocomplete

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


async def search(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
) -> IdunnAutocomplete:
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
    bragi_response = await bragi_client.autocomplete(query, extra)
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
