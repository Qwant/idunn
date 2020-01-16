import requests
import logging
from datetime import datetime, timedelta
from starlette.responses import JSONResponse
from starlette.requests import QueryParams
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from shapely.geometry import Point
from idunn import settings
from idunn.utils.geometry import city_surrounds_polygons
from idunn.places.base import BasePlace
from .models import DirectionsResponse

logger = logging.getLogger(__name__)

COMBIGO_SUPPORTED_LANGUAGES = {"en", "es", "de", "fr", "it"}


class MapboxAPIExtraParams(BaseModel):
    steps: str = "true"
    alternatives: str = "true"
    overview: str = "full"
    geometries: str = "geojson"
    exclude: Optional[str]


class DirectionsClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = settings["USER_AGENT"]

        self.combigo_session = requests.Session()
        self.combigo_session.headers["x-api-key"] = settings["COMBIGO_API_KEY"]
        self.combigo_session.headers["User-Agent"] = settings["USER_AGENT"]

        self.request_timeout = float(settings["DIRECTIONS_TIMEOUT"])

    @property
    def QWANT_BASE_URL(self):
        return settings["QWANT_DIRECTIONS_API_BASE_URL"]

    @property
    def COMBIGO_BASE_URL(self):
        return settings["COMBIGO_API_BASE_URL"]

    @property
    def MAPBOX_API_ENABLED(self):
        return bool(settings["MAPBOX_DIRECTIONS_ACCESS_TOKEN"])

    @staticmethod
    def is_in_allowed_zone(mode: str, from_place: BasePlace, to_place: BasePlace):
        if mode == "publictransport" and settings["PUBLIC_TRANSPORTS_RESTRICT_TO_CITIES"]:
            from_coord = from_place.get_coord()
            to_coord = to_place.get_coord()
            return any(
                all(
                    city_surrounds_polygons[city].contains(point)
                    for point in [
                        Point(from_coord['lon'], from_coord['lat']),
                        Point(to_coord['lon'], to_coord['lat']),
                    ]
                )
                for city in settings["PUBLIC_TRANSPORTS_RESTRICT_TO_CITIES"].split(",")
            )

        return True

    def directions_mapbox(self, start, end, mode, lang, extra=None):
        if extra is None:
            extra = {}

        start_coord = start.get_coord()
        start_lon, start_lat = start_coord["lon"], start_coord["lat"]
        end_coord = end.get_coord()
        end_lon, end_lat = end_coord["lon"], end_coord["lat"]

        base_url = settings["MAPBOX_DIRECTIONS_API_BASE_URL"]
        response = self.session.get(
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
                "Got error from mapbox API. " "Status: %s, Body: %s",
                response.status_code,
                response.text,
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        response.raise_for_status()
        return DirectionsResponse(status="success", data=response.json())

    def directions_qwant(self, start, end, mode, lang, extra=None):
        if not self.QWANT_BASE_URL:
            raise HTTPException(
                status_code=501, detail=f"Directions API is currently unavailable for mode {mode}"
            )

        if extra is None:
            extra = {}
        start_coord = start.get_coord()
        start_lon, start_lat = start_coord["lon"], start_coord["lat"]
        end_coord = end.get_coord()
        end_lon, end_lat = end_coord["lon"], end_coord["lat"]

        response = self.session.get(
            f"{self.QWANT_BASE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}",
            params={
                "type": mode,
                "language": lang,
                **MapboxAPIExtraParams(**extra).dict(exclude_none=True),
            },
            timeout=self.request_timeout,
        )

        if 400 <= response.status_code < 500:
            # Proxy client errors
            return JSONResponse(content=response.json(), status_code=response.status_code)
        response.raise_for_status()
        return DirectionsResponse(**response.json())

    def place_to_combigo_location(self, place, lang):
        location = {"lat": place.get_coord()["lat"], "lng": place.get_coord()["lon"]}
        if place.PLACE_TYPE != "latlon":
            name = place.get_name(lang)
            if name:
                location["name"] = name

        if place.get_class_name() in ("railway", "bus"):
            location["type"] = "publictransport"

        return location

    def directions_combigo(self, start, end, mode, lang):
        if not self.COMBIGO_BASE_URL:
            raise HTTPException(
                status_code=501, detail=f"Directions API is currently unavailable for mode {mode}"
            )

        if "_" in lang:
            # Combigo does not handle long locale format
            lang = lang[: lang.find("_")]

        if lang not in COMBIGO_SUPPORTED_LANGUAGES:
            lang = "en"

        response = self.combigo_session.post(
            f"{self.COMBIGO_BASE_URL}/journey",
            params={"lang": lang},
            json={
                "locations": [
                    self.place_to_combigo_location(start, lang),
                    self.place_to_combigo_location(end, lang),
                ],
                "type_include": mode,
                "dTime": (datetime.utcnow() + timedelta(minutes=1)).isoformat(timespec="seconds"),
            },
            timeout=self.request_timeout,
        )
        response.raise_for_status()
        return DirectionsResponse(status="success", data=response.json())

    def get_directions(self, from_place, to_place, mode, lang, params: QueryParams):
        if not DirectionsClient.is_in_allowed_zone(mode, from_place, to_place):
            raise HTTPException(
                status_code=422, detail="requested path is not inside an allowed area",
            )

        method = self.directions_qwant
        kwargs = {"extra": params}
        if self.MAPBOX_API_ENABLED:
            method = self.directions_mapbox

        if mode in ("driving-traffic", "driving", "car"):
            mode = "driving-traffic"
        elif mode in ("cycling",):
            mode = "cycling"
        elif mode in ("walking", "walk"):
            mode = "walking"
        elif mode in ("publictransport", "taxi", "vtc", "carpool"):
            method = self.directions_combigo
            kwargs = {}
            mode = mode
        else:
            raise HTTPException(status_code=400, detail=f"unknown mode {mode}")

        method_name = method.__name__
        logger.info(
            f"Calling directions API '{method_name}'",
            extra={
                "method": method_name,
                "mode": mode,
                "lang": lang,
                "from_place": from_place.get_id(),
                "to_place": to_place.get_id(),
            },
        )
        return method(from_place, to_place, mode, lang, **kwargs)


directions_client = DirectionsClient()
