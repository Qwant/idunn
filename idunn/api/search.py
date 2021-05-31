import logging
from fastapi import Body, Depends

from idunn import settings
from idunn.api.geocoder import get_autocomplete
from idunn.utils.result_filter import ResultFilter
from idunn.instant_answer import normalize
from ..geocoder.models import ExtraParams, QueryParams, IdunnAutocomplete

logger = logging.getLogger(__name__)
result_filter = ResultFilter(match_word_prefix=True, min_matching_words=3)

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")


async def search(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
) -> IdunnAutocomplete:
    """
    Perform a query which is intended to display a relevant result directly (as
    opposed to `autocomplete` which gives a list of plausible results).

    Similarly to `instant_answer`, the result will need some quality checks.
    """
    # Fetch autocomplete results which will be filtered
    query.q = normalize(query.q)
    response = await get_autocomplete(query, extra)

    # When an intention is detected, it takes over on geocoding features
    if response.intentions:
        response.features = []
        return response

    # Filter relevent features
    feasible_features = result_filter.filter_bragi_features(query.q, response.dict()["features"])

    # Pick most relevant feature, if any
    if feasible_features:
        response.features = [feasible_features[0]]
    else:
        response.features = []

    return response
