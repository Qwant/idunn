from .pois import get_poi
from .places import get_place, get_place_latlon, handle_option
from .status import get_status
from .places_list import get_places_bbox, get_events_bbox
from .categories import get_all_categories
from .closest import closest_address
from .directions import get_directions
from ..utils.prometheus import (
    expose_metrics,
    expose_metrics_multiprocess,
    MonitoredAPIRoute as APIRoute,
)
from .geocoder import get_autocomplete


def get_metric_handler(settings):
    """Select the prometheus multiprocess mode or not"""
    if settings["PROMETHEUS_MULTIPROC"]:
        return expose_metrics_multiprocess
    return expose_metrics


def get_api_urls(settings):
    """Defines all endpoints
    and handlers to build response
    """
    metric_handler = get_metric_handler(settings)
    return [
        APIRoute("/metrics", metric_handler),
        APIRoute("/status", get_status),
        # Deprecated
        APIRoute("/pois/{id}", get_poi),
        APIRoute("/places", get_places_bbox),
        APIRoute("/places/latlon:{lat}:{lon}", get_place_latlon),
        APIRoute("/places/{id}", handle_option, methods=["OPTIONS"]),
        APIRoute("/places/{id}", get_place),
        APIRoute("/categories", get_all_categories),
        APIRoute("/reverse/{lat}:{lon}", closest_address),
        # Kuzzle events
        APIRoute("/events", get_events_bbox),
        # Directions
        APIRoute('/directions/{f_lon},{f_lat};{t_lon},{t_lat}',
            get_directions
        ),

        # Geocoding
        APIRoute('/autocomplete', get_autocomplete, methods=['GET', 'POST']),
    ]
