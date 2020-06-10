from fastapi import HTTPException, Query, Depends, Request, Response

from idunn import settings
from idunn.places import Latlon, place_from_id, InvalidPlaceId
from idunn.utils.rate_limiter import IdunnRateLimiter
from ..directions.client import directions_client


rate_limiter = IdunnRateLimiter(
    resource="idunn.api.directions",
    max_requests=int(settings["DIRECTIONS_RL_MAX_REQUESTS"]),
    expire=int(settings["DIRECTIONS_RL_EXPIRE"]),
)


def directions_request(request: Request, response: Response):
    """
    FastAPI Dependency
    Responsible for rate limit and cache headers for directions requests
    """
    rate_limiter.check_limit_per_client(request)
    response.headers["cache-control"] = "max-age={}".format(settings["DIRECTIONS_CLIENT_CACHE"])
    return request


def get_directions_with_coordinates(
    # URL values
    f_lon: float,
    f_lat: float,
    t_lon: float,
    t_lat: float,
    # Query parameters
    type: str,
    language: str = "en",
    # Request
    request: Request = Depends(directions_request),
):
    from_place = Latlon(f_lat, f_lon)
    to_place = Latlon(t_lat, t_lon)
    if not type:
        raise HTTPException(status_code=400, detail='"type" query param is required')
    return directions_client.get_directions(
        from_place, to_place, type, language, params=request.query_params
    )


def get_directions(
    # Query parameters
    origin: str = Query(..., description="Origin place id"),
    destination: str = Query(..., description="Destination place id"),
    type: str = Query(..., description="Transport mode"),
    language: str = Query("en", description="User language"),
    # Request
    request: Request = Depends(directions_request),
):
    rate_limiter.check_limit_per_client(request)
    try:
        from_place = place_from_id(origin)
        to_place = place_from_id(destination)
    except InvalidPlaceId as exc:
        raise HTTPException(status_code=404, detail=exc.message)

    return directions_client.get_directions(
        from_place, to_place, type, language, params=request.query_params
    )
