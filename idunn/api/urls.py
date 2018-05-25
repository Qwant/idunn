from apistar import Route
from .pois import get_poi


api_urls = [
    Route('/pois/{id}', 'GET', handler=get_poi)
]
