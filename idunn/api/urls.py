from apistar import Route

from .pois import get_poi
from .status import get_status


api_urls = [
    Route('/status', 'GET', handler=get_status),
    Route('/pois/{id}', 'GET', handler=get_poi),
]
