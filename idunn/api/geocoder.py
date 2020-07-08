import asyncio
from fastapi import Body, Depends
from shapely.geometry import Point
from ..geocoder.bragi_client import bragi_client
from ..geocoder.nlu_client import nlu_client
from ..geocoder.models import QueryParams, ExtraParams

from idunn import settings


nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")
autocomplete_nlu_shadow_enabled = settings["AUTOCOMPLETE_NLU_SHADOW_ENABLED"]


async def get_autocomplete(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
):
    async def get_intentions():
        if query.lang not in nlu_allowed_languages:
            return None

        if not query.nlu and not autocomplete_nlu_shadow_enabled:
            return None

        focus = None
        if query.lon and query.lat:
            focus = Point(query.lon, query.lat)

        return await nlu_client.get_intentions(text=query.q, lang=query.lang, focus=focus)

    autocomplete_response, intentions = await asyncio.gather(
        bragi_client.autocomplete(query, extra), get_intentions()
    )
    if intentions is not None and query.nlu:
        autocomplete_response["intentions"] = intentions
    return autocomplete_response
