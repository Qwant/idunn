from fastapi.routing import APIRoute

from .pois import get_poi
from .places import get_place, get_place_latlon, handle_option
from .status import get_status
from .places_list import get_places_bbox, get_events_bbox
from .categories import get_all_categories
from .closest import closest_address
from .directions import get_directions
from ..utils.prometheus import expose_metrics, expose_metrics_multiprocess


def get_metric_handler(settings):
    """Select the prometheus multiprocess mode or not"""
    if settings['PROMETHEUS_MULTIPROC']:
        return expose_metrics_multiprocess
    return expose_metrics


def get_api_urls(settings):
    """Defines all endpoints
    and handlers to build response
    """
    metric_handler = get_metric_handler(settings)
    sfloat = 'float(signed=True)' # Werkzeug rule to allow negative floats
    return [
        APIRoute('/metrics', metric_handler),
        APIRoute('/status', get_status),

        # Deprecated
        APIRoute('/pois/{id}', get_poi),

        # Werkzeug syntax is used to allow negative floats
        APIRoute('/places', get_places_bbox),
        APIRoute(f'/places/latlon:<{sfloat}:lat>:<{sfloat}:lon>', get_place_latlon),
        APIRoute('/places/{id}', handle_option, methods=['OPTIONS']),
        APIRoute('/places/{id}', get_place),

        APIRoute('/categories', get_all_categories),


        # Werkzeug syntax is used to allow negative floats
        APIRoute(f'/reverse/<{sfloat}:lat>:<{sfloat}:lon>', closest_address),

        # Kuzzle events
        APIRoute('/events', get_events_bbox),

        # Directions
        APIRoute(f'/directions/<{sfloat}:f_lon>,<{sfloat}:f_lat>;<{sfloat}:t_lon>,<{sfloat}:t_lat>',
            get_directions
        )
    ]
