from apistar import Route
from apistar_prometheus import expose_metrics, expose_metrics_multiprocess

from .pois import get_poi
from .places import get_place
from .status import get_status
from .places_list import get_places_bbox
from .events_list import get_events_bbox
from .categories import get_all_categories

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
        Route('/pois/{id}', 'GET', handler=get_poi),
        Route('/places/{id}', 'GET', handler=get_place),
        Route('/categories', 'GET', handler=get_all_categories),
        Route('/places', 'GET', handler=get_places_bbox),
        Route('/events', 'GET', handler=get_events_bbox)
    ]
