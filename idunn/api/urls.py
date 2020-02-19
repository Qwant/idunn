from .pois import get_poi
from .places import get_place, get_place_latlon, handle_option
from .status import get_status
from .places_list import get_places_bbox, get_events_bbox
from .categories import get_all_categories
from .closest import closest_address
from ..directions.models import DirectionsResponse
from .geocoder import get_autocomplete
from ..geocoder.models import GeocodeJson
from .directions import get_directions_with_coordinates, get_directions
from ..utils.prometheus import (
    expose_metrics,
    expose_metrics_multiprocess,
    MonitoredAPIRoute as APIRoute,
)


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
        APIRoute("/metrics", metric_handler, include_in_schema=False),
        APIRoute("/status", get_status, include_in_schema=False),
        # Deprecated POI route
        APIRoute("/pois/{id}", get_poi, deprecated=True),
        # Places
        APIRoute("/places", get_places_bbox),
        APIRoute("/places/latlon:{lat}:{lon}", get_place_latlon),
        APIRoute("/places/{id}", handle_option, methods=["OPTIONS"], include_in_schema=False),
        APIRoute("/places/{id}", get_place),
        # Categories
        APIRoute("/categories", get_all_categories),
        # Reverse
        APIRoute("/reverse/{lat}:{lon}", closest_address),
        # Kuzzle events
        APIRoute("/events", get_events_bbox),
        # Directions
        APIRoute(
            "/directions/{f_lon},{f_lat};{t_lon},{t_lat}",
            get_directions_with_coordinates,
            response_model=DirectionsResponse,
            responses={422: {"description": "Requested Path Not Allowed."}},
        ),
        APIRoute(
            "/directions",
            get_directions,
            response_model=DirectionsResponse,
            responses={422: {"description": "Requested Path Not Allowed."}},
        ),
        # Geocoding
        APIRoute(
            "/autocomplete",
            get_autocomplete,
            methods=["GET", "POST"],
            response_model=GeocodeJson,
            response_model_exclude_unset=True,
        ),
    ]
