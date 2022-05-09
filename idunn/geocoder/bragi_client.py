import logging
import httpx
from json.decoder import JSONDecodeError
import pydantic
from fastapi import HTTPException

from idunn import settings
from .models import AutocompleteQueryParams, ExtraParams

logger = logging.getLogger(__name__)


async def get_explain_error(response):
    try:
        explain = response.json()["long"]
    except (IndexError, JSONDecodeError):
        explain = response.text
    logger.error(
        'Request to Bragi returned with unexpected status %d: "%s"',
        response.status_code,
        explain,
    )
    raise HTTPException(503, "Unexpected geocoder error")


class BragiClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            verify=settings["VERIFY_HTTPS"],
            limits=httpx.Limits(max_connections=int(settings["BRAGI_MAX_CONNECTIONS"])),
        )

    async def search(self, query: AutocompleteQueryParams):
        url = settings["BRAGI_BASE_URL"] + "/search"
        params = query.bragi_query_dict()
        try:
            response = await self.client.get(url, params=params)
        except httpx.ConnectTimeout as exc:
            logger.error("Request to Bragi %s failed with timeout", url, exc_info=True)
            raise HTTPException(503, "Server error: geocoder timeout") from exc

        if response.status_code != httpx.codes.OK:
            await get_explain_error(response)

        try:
            return response.json()
        except (JSONDecodeError, pydantic.ValidationError) as exc:
            logger.exception("Search invalid response")
            raise HTTPException(503, "Invalid response from the geocoder") from exc

    async def autocomplete(
        self, query: AutocompleteQueryParams, extra: ExtraParams = ExtraParams()
    ):
        params = query.bragi_query_dict()
        body = None
        if extra.shape:
            body = extra.dict()
        return await self.raw_autocomplete(params, body)

    async def raw_autocomplete(self, params, body=None):
        url = settings["BRAGI_BASE_URL"] + "/autocomplete"
        logger.info(url)
        try:
            if body:
                response = await self.client.post(url, params=params, json=body)
            else:
                response = await self.client.get(url, params=params)
        except httpx.ConnectTimeout as exc:
            logger.error("Request to Bragi %s failed with timeout", url, exc_info=True)
            raise HTTPException(503, "Server error: geocoder timeout") from exc

        if response.status_code != httpx.codes.OK:
            await get_explain_error(response)

        try:
            return response.json()
        except (JSONDecodeError, pydantic.ValidationError) as exc:
            logger.exception("Autocomplete invalid response")
            raise HTTPException(503, "Invalid response from the geocoder") from exc

    async def pois_query_in_bbox(self, query, bbox, limit, lang=None):
        query_params = {"q": query, "lang": lang, "limit": limit, "type[]": "poi"}
        xmin, ymin, xmax, ymax = bbox
        shape = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax], [xmin, ymin]]
                ],
            },
            "properties": {},
        }
        return await self.raw_autocomplete(params=query_params, body={"shape": shape})


bragi_client = BragiClient()
