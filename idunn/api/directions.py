from apistar.http import QueryParams, Request
from apistar.exceptions import BadRequest

from idunn import settings
from idunn.utils.rate_limiter import IdunnRateLimiter
from ..directions.client import directions_client

rate_limiter = IdunnRateLimiter(
    resource='idunn.api.directions',
    max_requests=int(settings['DIRECTIONS_RL_MAX_REQUESTS']),
    expire=int(settings['DIRECTIONS_RL_EXPIRE'])
)

def get_directions(f_lon, f_lat, t_lon, t_lat, params: QueryParams, request: Request):
    rate_limiter.check_limit_per_client(request)

    from_position = (f_lon, f_lat)
    to_position = (t_lon, t_lat)
    params_dict = dict(params)
    mode = params_dict.pop('type', '')
    lang = params_dict.pop('language', '') or 'en'

    if not mode:
        raise BadRequest('"type" query param is required')

    return directions_client.get_directions(
        from_position, to_position, mode=mode, lang=lang
    )
