import logging
from typing import Optional
from httpx import AsyncClient
from fastapi import Header, HTTPException
from idunn import settings

logger = logging.getLogger(__name__)

if settings["BANCHECK_ENABLED"]:
    ban_check_http = AsyncClient(
        base_url=settings["QWANT_API_BASE_URL"],
        timeout=float(settings["BANCHECK_TIMEOUT"]),
    )
else:
    ban_check_http = None


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
            raise Exception(f"Got invalid status {repr(response_status)} from ban check")
        is_client_banned = bool(response_data.get("data"))
        if is_client_banned:
            raise HTTPException(status_code=429)
    except Exception as err:
        logger.error("Failed to check client is not banned", exc_info=True)
        raise HTTPException(status_code=503) from err
