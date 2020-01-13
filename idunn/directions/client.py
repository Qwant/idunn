import requests
import logging
from datetime import datetime, timedelta
from starlette.responses import JSONResponse
from starlette.requests import QueryParams
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from idunn import settings
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

    def directions_mapbox(self, start, end, mode, lang, extra=None):
        if extra is None:
            extra = {}

        start_lon, start_lat = start
        end_lon, end_lat = end
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
            return JSONResponse(content=response.json(), status_code=response.status_code,)
        response.raise_for_status()
        return DirectionsResponse(status="success", data=response.json())

    def directions_qwant(self, start, end, mode, lang, extra=None):
        if not self.QWANT_BASE_URL:
            raise HTTPException(
                status_code=501, detail=f"Directions API is currently unavailable for mode {mode}",
            )

        if extra is None:
            extra = {}
        start_lon, start_lat = start
        end_lon, end_lat = end

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
            return JSONResponse(content=response.json(), status_code=response.status_code,)
        response.raise_for_status()
        return DirectionsResponse(**response.json())

    def directions_combigo(self, start, end, mode, lang):
        if not self.COMBIGO_BASE_URL:
            raise HTTPException(
                status_code=501, detail=f"Directions API is currently unavailable for mode {mode}",
            )

        start_lon, start_lat = start
        end_lon, end_lat = end

        if "_" in lang:
            # Combigo does not handle long locale format
            lang = lang[: lang.find("_")]

        if lang not in COMBIGO_SUPPORTED_LANGUAGES:
            lang = "en"

        response = self.combigo_session.post(
            f"{self.COMBIGO_BASE_URL}/journey",
            params={"lang": lang,},
            json={
                "locations": [
                    {"lat": start_lat, "lng": start_lon},
                    {"lat": end_lat, "lng": end_lon},
                ],
                "type_include": mode,
                "dTime": (datetime.utcnow() + timedelta(minutes=1)).isoformat(timespec="seconds"),
            },
            timeout=self.request_timeout,
        )
        response.raise_for_status()
        return DirectionsResponse(status="success", data=response.json())

    def get_directions(self, from_loc, to_loc, mode, lang, params: QueryParams):
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
            raise HTTPException(
                status_code=400, detail=f"unknown mode {mode}",
            )

        method_name = method.__name__
        logger.info(
            f"Calling directions API '{method_name}'",
            extra={
                "method": method_name,
                "mode": mode,
                "lang": lang,
                "from": from_loc,
                "to": to_loc,
            },
        )
        return method(from_loc, to_loc, mode, lang, **kwargs).dict(by_alias=True)


directions_client = DirectionsClient()
