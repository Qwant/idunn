import httpx
import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shapely.geometry import Point
from starlette.requests import QueryParams
from typing import Callable, Optional


from idunn import settings
from idunn.datasources.hove.client import client as hove_client
from idunn.directions.models import DirectionsResponse, IdunnTransportMode
from idunn.utils.geometry import city_surrounds_polygons
from idunn.places.base import BasePlace
from .models import DirectionsResponse
from ..geocoder.models import QueryParams

logger = logging.getLogger(__name__)


class MapboxAPIExtraParams(BaseModel):
    steps: str = "true"
    alternatives: str = "true"
    overview: str = "full"
    geometries: str = "geojson"
    exclude: Optional[str]


class DirectionsClient:
    def __init__(self):
        self.session = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])
        self.session.headers["User-Agent"] = settings["USER_AGENT"]
        self.request_timeout = float(settings["DIRECTIONS_TIMEOUT"])

    def get_method_for_mode(self, mode: IdunnTransportMode) -> Callable:
        methods = {
            "mapbox": self.directions_mapbox,
            "hove": hove_client.directions_hove,
        }

        match mode:
            case IdunnTransportMode.CAR:
                return methods[settings["DIRECTIONS_PROVIDER_DRIVE"]]
            case IdunnTransportMode.BIKE:
                return methods[settings["DIRECTIONS_PROVIDER_CYCLE"]]
            case IdunnTransportMode.WALKING:
                return methods[settings["DIRECTIONS_PROVIDER_WALK"]]
            case IdunnTransportMode.PUBLICTRANSPORT:
                return methods[settings["DIRECTIONS_PROVIDER_PUBLICTRANSPORT"]]

    @staticmethod
    def is_in_allowed_zone(mode: str, from_place: BasePlace, to_place: BasePlace):
        if mode == "publictransport" and settings["PUBLIC_TRANSPORTS_RESTRICT_TO_CITIES"]:
            from_coord = from_place.get_coord()
            to_coord = to_place.get_coord()
            return any(
                all(
                    city_surrounds_polygons[city].contains(point)
                    for point in [
                        Point(from_coord["lon"], from_coord["lat"]),
                        Point(to_coord["lon"], to_coord["lat"]),
                    ]
                )
                for city in settings["PUBLIC_TRANSPORTS_RESTRICT_TO_CITIES"].split(",")
            )
        return True

    @staticmethod
    def place_to_url_coords(place):
        coord = place.get_coord()
        lat, lon = coord["lat"], coord["lon"]
        return (f"{lon:.5f}", f"{lat:.5f}")

    async def directions_mapbox(self, start, end, mode: IdunnTransportMode, lang, extra=None):
        mode = mode.to_mapbox_query_param()

        if extra is None:
            extra = {}

        start_lon, start_lat = self.place_to_url_coords(start)
        end_lon, end_lat = self.place_to_url_coords(end)

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
        data["context"] = {"start_tz": start.get_tz(), "end_tz": end.get_tz()}
        return DirectionsResponse(status="success", data=data)

    async def get_directions(self, from_place, to_place, mode, lang, params: QueryParams):
        if not DirectionsClient.is_in_allowed_zone(mode, from_place, to_place):
            raise HTTPException(
                status_code=422,
                detail="requested path is not inside an allowed area",
            )

        idunn_mode = IdunnTransportMode.parse(mode)

        if idunn_mode is None:
            raise HTTPException(status_code=400, detail=f"unknown mode {mode}")

        method = self.get_method_for_mode(idunn_mode)
        method_name = method.__name__

        logger.info(
            "Calling directions API '%s'",
            method_name,
            extra={
                "method": method_name,
                "mode": idunn_mode,
                "lang": lang,
                "from_place": from_place.get_id(),
                "to_place": to_place.get_id(),
            },
        )

        # pylint: disable = not-callable
        return await method(from_place, to_place, idunn_mode, lang, params)


directions_client = DirectionsClient()
