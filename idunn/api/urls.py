from apistar import Route

from .pois import get_poi
from .status import get_status
from apistar_prometheus import expose_metrics

api_urls = [
    Route('/metrics', 'GET', handler=expose_metrics),
    Route('/status', 'GET', handler=get_status),
    Route('/pois/{id}', 'GET', handler=get_poi),
]
