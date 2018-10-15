from apistar import Route

from .pois import get_poi
from .places import get_place
from .status import get_status
from apistar_prometheus import expose_metrics, expose_metrics_multiprocess

def get_metric_handler(settings):
    if settings['PROMETHEUS_MULTIPROC']:
        return expose_metrics_multiprocess
    return expose_metrics

def get_api_urls(settings):
    metric_handler = get_metric_handler(settings)
    return [
        Route('/metrics', 'GET', handler=metric_handler),
        Route('/status', 'GET', handler=get_status),
        Route('/pois/{id}', 'GET', handler=get_poi),
        Route('/places/{id}', 'GET', handler=get_place),
    ]
