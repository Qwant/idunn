import logging
import httpx
from datetime import datetime
from fastapi import HTTPException
from shapely.geometry import Point
from typing import Optional

from idunn import settings
from idunn.geocoder.models.params import QueryParams
from idunn.places.base import BasePlace
from idunn.utils.geometry import city_surrounds_polygons
from .models import HoveResponse
from ..abs_client import AbsDirectionsClient
from ..mapbox.models import IdunnTransportMode


DIRECT_PATH_MAX_DURATION = 86400  # 24h
MIN_NB_JOURNEYS = 2
MAX_NB_JOURNEYS = 5
FREE_RADIUS = 50  # meters

logger = logging.getLogger(__name__)


class HoveClient(AbsDirectionsClient):
    def __init__(self):
        self.api_url = settings["HOVE_API_BASE_URL"]
        self.disabled_cities = settings["HOVE_PT_DISABLE_CITIES"].split(",")
        self.session = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])
        self.session.headers["User-Agent"] = settings["USER_AGENT"]

    @staticmethod
    def client_name() -> str:
        return "hove"

    @property
    def API_ENABLED(self):  # pylint: disable = invalid-name
        return bool(settings["HOVE_API_TOKEN"])

    def pt_enabled_for_coord(self, place: dict) -> bool:
        point = Point(place["lat"], place["lon"])

        return not any(
            city_surrounds_polygons[city].contains(point) for city in self.disabled_cities
        )

    async def get_directions(
        self,
        from_place: BasePlace,
        to_place: BasePlace,
        mode: IdunnTransportMode,
        _lang: str,
        arrive_by: Optional[datetime],
        depart_at: Optional[datetime],
        _extra: Optional[QueryParams] = None,
    ) -> HoveResponse:
        if not self.API_ENABLED:
            raise HTTPException(
                status_code=501,
                detail=f"Directions API is currently unavailable for mode {mode}",
            )

        from_place = from_place.get_coord()
        to_place = to_place.get_coord()
        date_time = arrive_by or depart_at

        pt_disabled_for_coords = mode == IdunnTransportMode.PUBLICTRANSPORT and (
            not self.pt_enabled_for_coord(from_place) or not self.pt_enabled_for_coord(to_place)
        )

        if pt_disabled_for_coords:
            logger.info(
                "Invalid coordinates for public transports with Hove: %s %s",
                from_place,
                to_place,
            )

            raise HTTPException(404, detail="public transports are disabled in this city")

        params = {
            "from": f"{from_place['lon']};{from_place['lat']}",
            "to": f"{to_place['lon']};{to_place['lat']}",
            "free_radius_from": FREE_RADIUS,
            "free_radius_to": FREE_RADIUS,
            "max_walking_direct_path_duration": DIRECT_PATH_MAX_DURATION,
            "max_bike_direct_path_duration": DIRECT_PATH_MAX_DURATION,
            "max_car_no_park_direct_path_duration": DIRECT_PATH_MAX_DURATION,
            "min_nb_journeys": MIN_NB_JOURNEYS,
            "max_nb_journeys": MAX_NB_JOURNEYS,
            **(
                {"direct_path": "none"}
                if mode == IdunnTransportMode.PUBLICTRANSPORT
                else {
                    "direct_path_mode[]": mode.to_hove(),
                    "direct_path": "only_with_alternatives",
                }
            ),
            **(
                {
                    "datetime": date_time.isoformat(),
                    "datetime_represents": "arrival" if arrive_by else "departure",
                }
                if date_time
                else {}
            ),
        }

        response = await self.session.get(
            self.api_url,
            params=params,
            headers={"Authorization": settings["HOVE_API_TOKEN"]},
        )

        if 400 <= response.status_code < 500:
            logger.info(
                "Got error from Hove API. Status: %s, Body: %s",
                response.status_code,
                response.text,
            )
            raise HTTPException(response.status_code, detail=response.json())

        response.raise_for_status()
        return HoveResponse(**response.json()).as_api_response()
