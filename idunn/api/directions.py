from datetime import datetime
from fastapi import HTTPException, Query, Path, Request, Response, Depends
from pydantic import confloat
from typing import Optional

from idunn import settings
from idunn.places import Latlon
from idunn.places.exceptions import IdunnPlaceError
from ..datasources.directions import directions_client
from ..utils.place import place_from_id


def directions_request(request: Request, response: Response):
    """
    FastAPI Dependency
    Responsible for rate limit and cache headers for directions requests
    """
    response.headers["cache-control"] = f"max-age={settings['DIRECTIONS_CLIENT_CACHE']}"
    return request


async def get_directions_with_coordinates(
    # URL values
    f_lon: confloat(ge=-180, le=180) = Path(title="Origin point longitude"),
    f_lat: confloat(ge=-90, le=90) = Path(title="Origin point latitude"),
    t_lon: confloat(ge=-180, le=180) = Path(title="Destination point longitude"),
    t_lat: confloat(ge=-90, le=90) = Path(title="Destination point latitude"),
    # Query parameters
    type: str = Query(..., description="Transport mode"),
    language: str = "en",
    # Time parameters
    arrive_by: Optional[datetime] = Query(None, title="Local arrival time"),
    depart_at: Optional[datetime] = Query(None, title="Local departure time"),
    # Request
    request: Request = Depends(directions_request),
):
    """Get directions to get from a point to another."""
    from_place = Latlon(f_lat, f_lon)
    to_place = Latlon(t_lat, t_lon)

    if arrive_by and depart_at:
        raise HTTPException(
            status_code=400,
            detail="`arrive_by` and `depart_at` can't both be specified",
        )

    if not type:
        raise HTTPException(status_code=400, detail='"type" query param is required')

    return await directions_client.get_directions(
        from_place, to_place, type, language, arrive_by, depart_at, extra=request.query_params
    )


async def get_directions(
    # Query parameters
    origin: str = Query(..., description="Origin place id."),
    destination: str = Query(..., description="Destination place id."),
    type: str = Query(..., description="Transport mode."),
    language: str = Query("en", description="User language."),
    # Time parameters
    arrive_by: Optional[datetime] = Query(None, title="Local arrival time"),
    depart_at: Optional[datetime] = Query(None, title="Local departure time"),
    # Request
    request: Request = Depends(directions_request),
):
    """Get directions to get from a places to another."""
    try:
        from_place = place_from_id(origin, language, follow_redirect=True)
        to_place = place_from_id(destination, language, follow_redirect=True)
    except IdunnPlaceError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    if arrive_by and depart_at:
        raise HTTPException(
            status_code=400,
            detail="`arrive_by` and `depart_at` can't both be specified",
        )

    return await directions_client.get_directions(
        from_place, to_place, type, language, arrive_by, depart_at, extra=request.query_params
    )
