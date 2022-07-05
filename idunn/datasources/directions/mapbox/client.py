import httpx
import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Tuple

from idunn import settings
from idunn.geocoder.models.params import QueryParams
from .. import AbsDirectionsClient
from ..mapbox.models import DirectionsResponse, IdunnTransportMode
from idunn.places.base import BasePlace

logger = logging.getLogger(__name__)


class MapboxAPIExtraParams(BaseModel):
    steps: str = "true"
    alternatives: str = "true"
    overview: str = "full"
    geometries: str = "geojson"
    exclude: Optional[str]


class MapboxClient(AbsDirectionsClient):
    def __init__(self):
        self.session = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])
        self.session.headers["User-Agent"] = settings["USER_AGENT"]
        self.request_timeout = float(settings["DIRECTIONS_TIMEOUT"])

    @staticmethod
    def client_name() -> str:
        return "mapbox"

    @property
    def API_ENABLED(self) -> bool:  # pylint: disable = invalid-name
        return bool(settings["MAPBOX_DIRECTIONS_ACCESS_TOKEN"])

    @staticmethod
    def place_to_url_coords(place: BasePlace) -> Tuple[str, str]:
        coord = place.get_coord()
        lat, lon = coord["lat"], coord["lon"]
        return (f"{lon:.5f}", f"{lat:.5f}")

    async def get_directions(
        self,
        from_place: BasePlace,
        to_place: BasePlace,
        mode: IdunnTransportMode,
        lang: str,
        extra: Optional[QueryParams] = None,
    ) -> DirectionsResponse:
        if not self.API_ENABLED:
            raise HTTPException(
                status_code=501,
                detail=f"Directions API is currently unavailable for mode {mode}",
            )

        mode = mode.to_mapbox_query_param()

        if extra is None:
            extra = {}

        start_lon, start_lat = self.place_to_url_coords(from_place)
        end_lon, end_lat = self.place_to_url_coords(to_place)

        base_url = settings["MAPBOX_DIRECTIONS_API_BASE_URL"]
        response = await self.session.get(
            f"{base_url}/{mode}/{start_lon},{start_lat};{end_lon},{end_lat}",
            params={
                "language": lang,
                "access_token": settings["MAPBOX_DIRECTIONS_ACCESS_TOKEN"],
                **MapboxAPIExtraParams(**extra).dict(exclude_none=True),
            },
            timeout=self.request_timeout,
        )

        if 400 <= response.status_code < 500:
            # Proxy client errors
            logger.info(
                "Got error from mapbox API. Status: %s, Body: %s",
                response.status_code,
                response.text,
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)

        response.raise_for_status()
        data = response.json()
        data["context"] = {"start_tz": from_place.get_tz(), "end_tz": to_place.get_tz()}
        return DirectionsResponse(status="success", data=data)
