from fastapi import Depends

from .pois import get_poi
from .places import get_place, get_place_latlon
from .status import get_status
from .places_list import get_places_bbox, get_events_bbox, PlacesBboxResponse
from .categories import AllCategoriesResponse, get_all_categories
from .closest import closest_address
from ..directions.models import DirectionsResponse
from .geocoder import get_autocomplete_response
from ..geocoder.models import IdunnAutocomplete
from .directions import get_directions_with_coordinates, get_directions
from .urlsolver import follow_redirection
from .instant_answer import get_instant_answer, InstantAnswerResponse
from ..places.place import Address, Place
from .search import search
from ..utils.prometheus import (
    expose_metrics,
    expose_metrics_multiprocess,
    MonitoredAPIRoute as APIRoute,
)
from ..utils.ban_check import check_banned_client
from ..utils.rate_limiter import rate_limiter_dependency


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
        APIRoute("/pois/{id}", get_poi, deprecated=True, include_in_schema=False),
        # Places
        APIRoute(
            "/places",
            get_places_bbox,
            dependencies=[
                rate_limiter_dependency(
                    resource="idunn.get_places_bbox",
                    max_requests=int(settings["LIST_PLACES_RL_MAX_REQUESTS"]),
                    expire=int(settings["LIST_PLACES_RL_EXPIRE"]),
                )
            ],
            response_model=PlacesBboxResponse,
            responses={400: {"description": "Client Error in query params"}},
        ),
        APIRoute("/places/latlon:{lat}:{lon}", get_place_latlon, response_model=Place),
        APIRoute("/places/{id}", get_place, response_model=Place),
        # Categories
        APIRoute("/categories", get_all_categories, response_model=AllCategoriesResponse),
        # Reverse
        APIRoute("/reverse/{lat}:{lon}", closest_address, response_model=Address),
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
            get_autocomplete_response,
            methods=["GET", "POST"],
            response_model=IdunnAutocomplete,
        ),
        APIRoute(
            "/search",
            search,
            methods=["GET", "POST"],
            response_model=IdunnAutocomplete,
            response_model_exclude_unset=True,
        ),
        # Solve URLs
        APIRoute(
            "/redirect",
            follow_redirection,
            status_code=307,
            responses={
                403: {"description": "Wrong URL hash."},
                404: {"description": "The URL does not redirect."},
            },
        ),
        APIRoute(
            "/instant_answer",
            get_instant_answer,
            dependencies=[Depends(check_banned_client)],
            response_model=InstantAnswerResponse,
            responses={
                200: {"description": "Details about place(s) to display"},
                204: {"description": "No instant answer to display"},
            },
        ),
    ]
