from typing import List, Optional

from fastapi import Query, Depends
from pydantic import BaseModel, PositiveInt

from idunn import settings
from ..geocoder.client import geocoder_client
from ..geocoder.models import GeocodeJson, QueryParams, ExtraParams


def get_autocomplete(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = ExtraParams()
) -> GeocodeJson:
    return geocoder_client.autocomplete(query, extra)
