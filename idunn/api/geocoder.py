import asyncio
from fastapi import Body, Depends
from ..geocoder.bragi_client import bragi_client
from ..geocoder.nlu_client import nlu_client
from ..geocoder.models import QueryParams, ExtraParams


async def get_autocomplete(
    query: QueryParams = Depends(QueryParams), extra: ExtraParams = Body(ExtraParams())
):
    async def get_intentions():
        if not query.nlu:
            return None
        return await nlu_client.get_intentions(text=query.q, lang=query.lang)

    autocomplete_response, intentions = await asyncio.gather(
        bragi_client.autocomplete(query, extra),
        get_intentions()
    )
    if intentions is not None:
        autocomplete_response["intentions"] = intentions
    return autocomplete_response
