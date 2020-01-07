from typing import Optional

from fastapi import Query
from pydantic import BaseModel

from idunn import settings
from ..geocoder.client import geocoder_client


class ExtraParams(BaseModel):
    shape: dict = Query(None, title='restrict search inside of a polygon')


def get_autocomplete(
    extra: ExtraParams = ExtraParams(),
    query: str = Query(..., alias='q'),
    lon: Optional[float] = None,
    lat: Optional[float] = None,
    lang: str = settings['DEFAULT_LANGUAGE'],
    limit: int = 10,
):
    return geocoder_client.autocomplete(query, lang, limit, lon, lat, extra.shape)
