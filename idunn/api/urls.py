from apistar import Route
from apistar_prometheus import expose_metrics, expose_metrics_multiprocess

from .pois import get_poi
from .places import get_place, get_place_latlon
from .status import get_status
from .places_list import get_places_bbox, get_events_bbox
from .categories import get_all_categories
from .closest import closest_address

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
    return [
        Route('/metrics', 'GET', handler=metric_handler),
        Route('/status', 'GET', handler=get_status),

        # Deprecated
        Route('/pois/{id}', 'GET', handler=get_poi),

        # Werkzeug syntax is used to allow negative floats
        Route('/places/latlon:<float(signed=True):lat>:<float(signed=True):lon>', 'GET', handler=get_place_latlon),
        Route('/places/{id}', 'GET', handler=get_place),

        Route('/categories', 'GET', handler=get_all_categories),

        Route('/places', 'GET', handler=get_places_bbox),

        # Werkzeug syntax is used to allow negative floats
        Route('/reverse/<float(signed=True):lat>:<float(signed=True):lon>', 'GET', handler=closest_address),

        # Kuzzle events
        Route('/events', 'GET', handler=get_events_bbox),
    ]
