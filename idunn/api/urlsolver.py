import hmac
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from idunn import settings


client = httpx.AsyncClient()
base_url = settings.get("BASE_URL")
secret = settings.get("SECRET").encode()


def resolve_url(url: str) -> str:
    """
    Idunn's URL that can be provided to redirect to the same page as the input
    URL would.
    """
    return base_url + f"v1/redirect?url={quote(url, safe='')}&hash={hash_url(url)}"


def hash_url(url: str) -> str:
    """
    Hash of the URL that the client must provide in order to avoid abusive use
    of the endpoint.
    """
    return hmac.HMAC(key=secret, msg=url.encode(), digestmod="sha256").hexdigest()


async def follow_redirection(url: str, hash: str):
    if not hmac.compare_digest(hash_url(url), hash):
        raise HTTPException(403, detail="provided hash does not match the URL")

    response = await client.get(url, allow_redirects=False)
    response.raise_for_status()

    if response.status_code not in range(300, 400):
        raise HTTPException(404, detail="provided URL does not redirect")

    return RedirectResponse(response.headers["Location"])
