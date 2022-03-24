import logging
from functools import lru_cache
from typing import Optional
from httpx import AsyncClient
from fastapi import Header, HTTPException
from idunn import settings

logger = logging.getLogger(__name__)


def get_ban_check_http():
    if settings["BANCHECK_ENABLED"]:
        return AsyncClient(
            base_url=settings["QWANT_API_BASE_URL"],
            timeout=float(settings["BANCHECK_TIMEOUT"]),
        )
    return None


ban_check_http = get_ban_check_http()


@lru_cache(maxsize=100)
async def check_banned_client(x_client_hash: Optional[str] = Header(None)):
    if ban_check_http is None:
        return
    if not x_client_hash:
        return

    try:
        response = await ban_check_http.get(
            "/v3/captcha/isban", params={"client_hash": x_client_hash}
        )
        response.raise_for_status()
        response_data = response.json()
        response_status = response_data.get("status")
        if response_status != "success":
            raise ValueError(f"Got invalid status {repr(response_status)} from ban check")
    except Exception as err:
        logger.error("Failed to check client is not banned", exc_info=True)
        raise HTTPException(status_code=503) from err

    is_client_banned = bool(response_data.get("data"))
    if is_client_banned:
        raise HTTPException(status_code=429)
