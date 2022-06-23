import logging
import requests
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shapely.geometry import Point
from starlette.requests import QueryParams
from typing import Optional


from idunn import settings
from idunn.datasources.hove.models import HoveResponse
from idunn.directions.models import DirectionsResponse, IdunnTransportMode
from idunn.utils.geometry import city_surrounds_polygons
from idunn.places.base import BasePlace

logger = logging.getLogger(__name__)


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
        self.request_timeout = float(settings["DIRECTIONS_TIMEOUT"])

    @property
    def MAPBOX_API_ENABLED(self):  # pylint: disable = invalid-name
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

    def directions_mapbox(self, start, end, mode, lang, extra=None):
        if extra is None:
            extra = {}

        start_lon, start_lat = self.place_to_url_coords(start)
        end_lon, end_lat = self.place_to_url_coords(end)

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
                "Got error from mapbox API. Status: %s, Body: %s",
                response.status_code,
                response.text,
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        response.raise_for_status()
        data = response.json()
        data["context"] = {"start_tz": start.get_tz(), "end_tz": end.get_tz()}
        return DirectionsResponse(status="success", data=data)

    def directions_qwant(self, start, end, mode, lang, extra=None):
        if not self.QWANT_BASE_URL:
            raise HTTPException(
                status_code=501, detail=f"Directions API is currently unavailable for mode {mode}"
            )

        if extra is None:
            extra = {}

        start_lon, start_lat = self.place_to_url_coords(start)
        end_lon, end_lat = self.place_to_url_coords(end)
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
        res = response.json()
        res["data"]["context"] = {"start_tz": start.get_tz(), "end_tz": end.get_tz()}
        return DirectionsResponse(**res)

    def directions_hove(self, start, end, mode: IdunnTransportMode, lang, extra=None):
        url = settings["HOVE_API_BASE_URL"]
        start = start.get_coord()
        end = end.get_coord()

        params = {
            "from": f"{start['lon']};{start['lat']}",
            "to": f"{end['lon']};{end['lat']}",
            "free_radius_from": 50,
            "free_radius_to": 50,
            "max_walking_direct_path_duration": 86400,
            "max_bike_direct_path_duration": 86400,
            "max_car_no_park_direct_path_duration": 86400,
            "min_nb_journeys": 2,
            "max_nb_journeys": 5,
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

        response = self.session.get(
            url,
            params=params,
            headers={"Authorization": settings["HOVE_API_TOKEN"]},
        )

        response.raise_for_status()
        return HoveResponse(**response.json())

    @staticmethod
    def place_to_combigo_location(place, lang):
        coord = place.get_coord()
        location = {"lat": coord["lat"], "lng": coord["lon"]}
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
        data = response.json()
        data["context"] = {"start_tz": start.get_tz(), "end_tz": end.get_tz()}
        return DirectionsResponse(status="success", data=data)

    def get_directions(self, from_place, to_place, mode, lang, params: QueryParams):
        if not self.MAPBOX_API_ENABLED:
            raise HTTPException(
                status_code=501, detail=f"Directions API is currently unavailable for mode {mode}"
            )

        if not DirectionsClient.is_in_allowed_zone(mode, from_place, to_place):
            raise HTTPException(
                status_code=422,
                detail="requested path is not inside an allowed area",
            )

        kwargs = {"extra": params}
        method = self.directions_mapbox

        if mode in ("driving-traffic", "driving", "car"):
            mode = "driving-traffic"
        elif mode in ("cycling",):
            mode = "cycling"
        elif mode in ("walking", "walk"):
            mode = "walking"
        else:
            raise HTTPException(status_code=400, detail=f"unknown mode {mode}")

        idunn_mode = IdunnTransportMode.parse(mode)
        res = self.directions_hove(from_place, to_place, idunn_mode, lang)
        return res.as_api_response()

        #  method_name = method.__name__
        #  logger.info(
        #      "Calling directions API '%s'",
        #      method_name,
        #      extra={
        #          "method": method_name,
        #          "mode": mode,
        #          "lang": lang,
        #          "from_place": from_place.get_id(),
        #          "to_place": to_place.get_id(),
        #      },
        #  )
        #  return method(from_place, to_place, mode, lang, **kwargs)


directions_client = DirectionsClient()
