import httpx
from fastapi import HTTPException
from typing import Optional

from idunn import settings
from idunn.datasources.directions import AbsDirectionsClient
from idunn.datasources.directions.mapbox.models import IdunnTransportMode
from idunn.geocoder.models.params import QueryParams
from idunn.places.base import BasePlace
from .models import HoveResponse


DIRECT_PATH_MAX_DURATION = 86400  # 24h
MIN_NB_JOURNEYS = 2
MAX_NB_JOURNEYS = 5
FREE_RADIUS = 50  # meters


class HoveClient(AbsDirectionsClient):
    def __init__(self):
        self.api_url = settings["HOVE_API_BASE_URL"]
        self.session = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])
        self.session.headers["User-Agent"] = settings["USER_AGENT"]

    @staticmethod
    def client_name() -> str:
        return "hove"

    @property
    def API_ENABLED(self):  # pylint: disable = invalid-name
        return bool(settings["HOVE_API_TOKEN"])

    async def get_directions(
        self,
        from_place: BasePlace,
        to_place: BasePlace,
        mode: IdunnTransportMode,
        _lang: str,
        _extra: Optional[QueryParams] = None,
    ) -> HoveResponse:
        if not self.API_ENABLED:
            raise HTTPException(
                status_code=501,
                detail=f"Directions API is currently unavailable for mode {mode}",
            )

        from_place = from_place.get_coord()
        to_place = to_place.get_coord()

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
        }

        if mode == IdunnTransportMode.PUBLICTRANSPORT:
            params.update({"direct_path": "none"})
        else:
            params.update(
                {
                    "direct_path_mode[]": mode.to_hove(),
                    "direct_path": "only",
                }
            )

        response = await self.session.get(
            self.api_url,
            params=params,
            headers={"Authorization": settings["HOVE_API_TOKEN"]},
        )

        response.raise_for_status()
        return HoveResponse(**response.json()).as_api_response()
