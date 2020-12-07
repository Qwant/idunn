from hashlib import sha1
from secrets import token_bytes
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from fastapi.responses import RedirectResponse


client = httpx.AsyncClient()

# Randomized seed used to hash addresses to solve, do not leek.
random_token = token_bytes(64)


def hash_url(url: str) -> str:
    """
    Hash of the URL that the client must provide in order to avoid abusive use
    of the endpoint.
    """
    return sha1(random_token + url.encode()).hexdigest()


async def follow_redirection(url: str, hash: str):
    if hash_url(url) != hash:
        raise HTTPException(403, detail="provided hash does not match the URL")

    response = await client.get(url, allow_redirects=False)
    response.raise_for_status()

    if response.status_code not in range(300, 400):
        raise HTTPException(404, detail="provided URL does not redirect")

    return RedirectResponse(response.headers["Location"])
