from fastapi import HTTPException, Query, Depends, Path, Request, Response
from pydantic import confloat

from idunn import settings
from idunn.places import Latlon
from idunn.places.exceptions import IdunnPlaceError
from idunn.utils.rate_limiter import IdunnRateLimiter
from ..directions.client import directions_client
from ..utils.place import place_from_id

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
    response.headers["cache-control"] = f"max-age={settings['DIRECTIONS_CLIENT_CACHE']}"
    return request


def get_directions_with_coordinates(
    # URL values
    f_lon: confloat(ge=-180, le=180) = Path(..., title="Origin point longitude"),
    f_lat: confloat(ge=-90, le=90) = Path(..., title="Origin point latitude"),
    t_lon: confloat(ge=-180, le=180) = Path(..., title="Destination point longitude"),
    t_lat: confloat(ge=-90, le=90) = Path(..., title="Destination point latitude"),
    # Query parameters
    type: str = Query(..., description="Transport mode"),
    language: str = "en",
    # Request
    request: Request = Depends(directions_request),
):
    """Get directions to get from a point to another."""
    from_place = Latlon(f_lat, f_lon)
    to_place = Latlon(t_lat, t_lon)
    if not type:
        raise HTTPException(status_code=400, detail='"type" query param is required')
    return directions_client.get_directions(
        from_place, to_place, type, language, params=request.query_params
    )


def get_directions(
    # Query parameters
    origin: str = Query(..., description="Origin place id."),
    destination: str = Query(..., description="Destination place id."),
    type: str = Query(..., description="Transport mode."),
    language: str = Query("en", description="User language."),
    # Request
    request: Request = Depends(directions_request),
):
    """Get directions to get from a places to another."""
    try:
        from_place = place_from_id(origin, language, follow_redirect=True)
        to_place = place_from_id(destination, language, follow_redirect=True)
    except IdunnPlaceError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    return directions_client.get_directions(
        from_place, to_place, type, language, params=request.query_params
    )
