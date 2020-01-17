from fastapi import Body, Depends, Query

from ..geocoder.client import geocoder_client
from ..geocoder.models import GeocodeJson, QueryParams, ExtraParams


def get_autocomplete(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
) -> GeocodeJson:
    return geocoder_client.autocomplete(query, extra)
