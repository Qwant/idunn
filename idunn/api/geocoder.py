from fastapi import Body, Depends, Query

from ..geocoder.client import geocoder_client
from ..geocoder.models import IdunnAutocomplete, QueryParams, ExtraParams


def get_autocomplete(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
) -> IdunnAutocomplete:
    return geocoder_client.autocomplete(query, extra)
