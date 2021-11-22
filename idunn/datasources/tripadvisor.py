import logging
from json import JSONDecodeError

import httpx
import pydantic
from fastapi import HTTPException

from idunn import settings

logger = logging.getLogger(__name__)

TA_API_BASE_URL = "https://api.tripadvisor.com/api/partner/3.0/synmeta-pricing"


class TripAdvisorAPI:
    TA_API_TIMEOUT = float(settings.get("TA_API_TIMEOUT"))

    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])

    async def get_hotel_pricing_by_hotel_id(self, params=None):
        try:
            response = await self.client.get(
                TA_API_BASE_URL,
                params=cleanup_empty_params(params),
                timeout=self.TA_API_TIMEOUT,
            )
        except httpx.ConnectTimeout as exc:
            logger.error("Request to TripAdvisor failed with timeout")
            raise HTTPException(503, "Server error: TripAdvisor API timeout") from exc

        if response.status_code != httpx.codes.OK:
            try:
                explain = response.json()["long"]
            except (IndexError, JSONDecodeError):
                explain = response.text
            logger.error(
                'Request to TripAdvisor returned with unexpected status %d: "%s"',
                response.status_code,
                explain,
            )
            raise HTTPException(503, "Unexpected tripadvisor api error")

        try:
            return response.json()
        except (JSONDecodeError, pydantic.ValidationError) as exc:
            logger.exception("Tripadvisor hotel pricing api invalid response")
            raise HTTPException(503, "Invalid response from the tripadvisor API") from exc


def cleanup_empty_params(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.
    This alters the input so you may wish to ``copy`` the dict first.
    """
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            cleanup_empty_params(value)
    return d  # For convenience


tripadvisor_api = TripAdvisorAPI()
