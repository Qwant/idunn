from fastapi import Depends

from .hotel_pricing import get_hotel_pricing
from .places import get_place, get_place_latlon
from .status import get_status
from .places_list import get_places_bbox, PlacesBboxResponse
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


def api_route(*args, **kwargs):
    kwargs["dependencies"] = kwargs.get("dependencies", []) + [Depends(check_banned_client)]
    return APIRoute(*args, **kwargs)


def get_api_urls(settings):
    """Defines all endpoints
    and handlers to build response
    """
    metric_handler = get_metric_handler(settings)

    rate_limiter_get_place = rate_limiter_dependency(
        resource="idunn.get_places_bbox",
        max_requests=int(settings["GET_PLACE_RL_MAX_REQUESTS"]),
        expire=int(settings["GET_PLACE_RL_EXPIRE"]),
    )

    rate_limiter_places_list = rate_limiter_dependency(
        resource="idunn.get_places_bbox",
        max_requests=int(settings["LIST_PLACES_RL_MAX_REQUESTS"]),
        expire=int(settings["LIST_PLACES_RL_EXPIRE"]),
    )

    rate_limiter_directions = rate_limiter_dependency(
        resource="idunn.api.directions",
        max_requests=int(settings["DIRECTIONS_RL_MAX_REQUESTS"]),
        expire=int(settings["DIRECTIONS_RL_EXPIRE"]),
    )

    return [
        api_route("/metrics", metric_handler, include_in_schema=False),
        api_route("/status", get_status, include_in_schema=False),
        # Places
        api_route(
            "/places",
            get_places_bbox,
            dependencies=[rate_limiter_places_list],
            response_model=PlacesBboxResponse,
            responses={400: {"description": "Client Error in query params"}},
        ),
        api_route(
            "/places/latlon:{lat}:{lon}",
            get_place_latlon,
            dependencies=[rate_limiter_get_place],
            response_model=Place,
        ),
        api_route(
            "/places/{id}",
            get_place,
            dependencies=[rate_limiter_get_place],
            response_model=Place,
        ),
        # Categories
        api_route("/categories", get_all_categories, response_model=AllCategoriesResponse),
        # Reverse
        api_route("/reverse/{lat}:{lon}", closest_address, response_model=Address),
        # TODO remove hotel_pricing endpoint on merge with master
        # TripAdvisor hotel
        api_route("/hotel_pricing", get_hotel_pricing),
        # Directions
        api_route(
            "/directions/{f_lon},{f_lat};{t_lon},{t_lat}",
            get_directions_with_coordinates,
            dependencies=[rate_limiter_directions],
            response_model=DirectionsResponse,
            responses={422: {"description": "Requested Path Not Allowed."}},
        ),
        api_route(
            "/directions",
            get_directions,
            dependencies=[rate_limiter_directions],
            response_model=DirectionsResponse,
            responses={422: {"description": "Requested Path Not Allowed."}},
        ),
        # Geocoding
        api_route(
            "/autocomplete",
            get_autocomplete_response,
            methods=["GET", "POST"],
            response_model=IdunnAutocomplete,
        ),
        api_route(
            "/search",
            search,
            methods=["GET", "POST"],
            response_model=IdunnAutocomplete,
            responses={
                204: {"description": "Empty search provided"},
            },
            response_model_exclude_unset=True,
        ),
        # Solve URLs
        api_route(
            "/redirect",
            follow_redirection,
            status_code=307,
            responses={
                403: {"description": "Wrong URL hash."},
                404: {"description": "The URL does not redirect."},
            },
        ),
        api_route(
            "/instant_answer",
            get_instant_answer,
            response_model=InstantAnswerResponse,
            responses={
                200: {"description": "Details about place(s) to display"},
                204: {"description": "No instant answer to display"},
            },
        ),
    ]
