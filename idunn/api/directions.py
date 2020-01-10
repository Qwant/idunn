from fastapi import HTTPException

from pydantic import constr

from shapely.geometry import Point

from starlette.requests import Request
from starlette.responses import Response

from idunn import settings
from idunn.utils.geometry import city_surrounds_polygons
from idunn.utils.rate_limiter import IdunnRateLimiter
from ..directions.client import directions_client

rate_limiter = IdunnRateLimiter(
    resource="idunn.api.directions",
    max_requests=int(settings["DIRECTIONS_RL_MAX_REQUESTS"]),
    expire=int(settings["DIRECTIONS_RL_EXPIRE"]),
)


def get_directions(
    response: Response,
    f_lon: float, f_lat: float, t_lon: float, t_lat: float, # URL values
    request: Request,
    type: constr(min_length=1),
    language: str = "en",  # query parameters
):
    rate_limiter.check_limit_per_client(request)

    from_position = (f_lon, f_lat)
    to_position = (t_lon, t_lat)

    if type in ("publictransport", "taxi", "vtc", "carpool"):
        allowed_zone = any(
            all(
                city_surrounds_polygons[city].contains(point)
                for point in [Point(*from_position), Point(*to_position)]
            )
            for city in settings["PUBLIC_TRANSPORTS_ALLOWED_CITIES"]
        )

        if not allowed_zone:
            raise HTTPException(
                status_code=422,
                detail="requested path is not inside an allowed area for public transports",
            )

    response.headers['cache-control'] = (
        'max-age={}'.format(settings['DIRECTIONS_CLIENT_CACHE'])
    )

    return directions_client.get_directions(
        from_position, to_position, type, language, params=request.query_params
    )
