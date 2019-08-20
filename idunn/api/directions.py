from apistar.http import QueryParams
from apistar.exceptions import BadRequest
from ..directions.client import directions_client


def get_directions(f_lon, f_lat, t_lon, t_lat, params: QueryParams):
    from_position = (f_lon, f_lat)
    to_position = (t_lon, t_lat)
    params_dict = dict(params)
    mode = params_dict.pop('type', '')
    lang = params_dict.pop('language', '') or 'en'

    if not mode:
        raise BadRequest('"type" query param is required')

    return directions_client.get_directions(from_position, to_position,
        mode=mode, lang=lang
    )
