from fastapi import Body, Depends
from ..geocoder.bragi_client import bragi_client
from ..geocoder.nlu_client import nlu_client
from ..geocoder.models import IdunnAutocomplete, QueryParams, ExtraParams


def get_autocomplete(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
) -> IdunnAutocomplete:
    autocomplete_response = bragi_client.autocomplete(query, extra)
    if query.nlu:
        autocomplete_response["intentions"] = nlu_client.get_intentions(
            text=query.q, lang=query.lang
        )
    return IdunnAutocomplete(**autocomplete_response)
