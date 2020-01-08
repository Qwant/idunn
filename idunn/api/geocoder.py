from typing import Optional

from fastapi import Query
from pydantic import BaseModel

from idunn import settings
from ..geocoder.client import geocoder_client


class ExtraParams(BaseModel):
    shape: dict = Query(None, title='restrict search inside of a polygon')


def get_autocomplete(
    extra: ExtraParams = ExtraParams(),
    query: str = Query(..., alias='q', title='query string'),
    lon: Optional[float] = Query(None, ge=-180, le=180, title='latitude for the focus'),
    lat: Optional[float] = Query(None, ge=-90, le=90, title='longitude for the focus'),
    lang: str = Query(settings['DEFAULT_LANGUAGE'], title='language'),
    limit: int = Query(10, ge=1, title='maximum number of results'),
):
    return geocoder_client.autocomplete(query, lang, limit, lon, lat, extra.shape)
