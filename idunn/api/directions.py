from fastapi import HTTPException

from starlette.requests import Request
from starlette.responses import JSONResponse


from idunn import settings
from idunn.utils.rate_limiter import IdunnRateLimiter
from ..directions.client import directions_client

rate_limiter = IdunnRateLimiter(
    resource='idunn.api.directions',
    max_requests=int(settings['DIRECTIONS_RL_MAX_REQUESTS']),
    expire=int(settings['DIRECTIONS_RL_EXPIRE'])
)

def get_directions(
    f_lon: float, f_lat: float, t_lon: float, t_lat: float, # URL values
    request: Request,
    type: str = '', language: str = 'en' # query parameters
):
    rate_limiter.check_limit_per_client(request)

    from_position = (f_lon, f_lat)
    to_position = (t_lon, t_lat)

    if not mode:
        raise HTTPException(status_code=401, detail='"type" query param is required')

    headers = {
        'cache-control': 'max-age={}'.format(settings['DIRECTIONS_CLIENT_CACHE'])
     }

    return JSONResponse(
        content=directions_client.get_directions(
            from_position, to_position, mode=type, lang=language
        ),
        headers=headers,
    )
