import logging
import httpx
from json.decoder import JSONDecodeError
import pydantic
from fastapi import HTTPException

from idunn import settings
from .models import QueryParams, ExtraParams

logger = logging.getLogger(__name__)


class BragiClient:
    def __init__(self):
        self.client = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])

    async def autocomplete(self, query: QueryParams, extra: ExtraParams):
        params = query.bragi_query_dict()
        body = None
        if extra.shape:
            body = extra.dict()
        return await self.raw_autocomplete(params, body)

    async def raw_autocomplete(self, params, body=None):
        url = settings["BRAGI_BASE_URL"] + "/autocomplete"
        if body:
            response = await self.client.post(url, params=params, json=body)
        else:
            response = await self.client.get(url, params=params)

        if response.status_code != httpx.codes.ok:
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

        try:
            return response.json()
        except (JSONDecodeError, pydantic.ValidationError) as e:
            logger.exception("Autocomplete invalid response")
            raise HTTPException(503, "Invalid response from the geocoder")

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
