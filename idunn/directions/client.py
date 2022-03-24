import requests
import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from pydantic.class_validators import validator

from shapely.geometry import Point
from idunn import settings
from idunn.utils.geometry import city_surrounds_polygons
from idunn.places.base import BasePlace
from .models import (
    DirectionsData,
    DirectionsResponse,
    DirectionsRoute,
    RouteLeg,
    RouteManeuver,
    RouteStep,
    TransportMode,
)

logger = logging.getLogger(__name__)


# Mapbox <-> Navitia correspondance
#  - route <-> journey
#  - leg <-> section
#  - step <-> single element of section ? Can be re-cut later ?


class Distances(BaseModel):
    bike: int
    car: int
    ridesharing: int
    taxi: int
    walking: int

    def overall(self):
        return self.bike + self.car + self.ridesharing + self.taxi + self.walking


class Coordinate(BaseModel):
    lat: float
    lon: float


class Instruction(BaseModel):
    direction: int
    duration: int
    instruction: str
    instruction_start_coordinate: Coordinate
    length: int
    name: str

    def as_api_route_step(self, mode, prev=Coordinate) -> RouteStep:
        RouteStep(
            maneuver=RouteManeuver(
                location=(
                    self.instruction_start_coordinate.lon,
                    self.instruction_start_coordinate.lat,
                ),
                instruction=self.instruction,
                # type, modifier ??
            ),
            duration=self.duration,
            distance=self.length,
            geometry={
                "coordinates": [
                    [prev.lon, prev.lat],
                    [self.instruction_start_coordinate.lon, self.instruction_start_coordinate.lat],
                ]
            },
            mode=mode,
        )


class Section(BaseModel):
    mode: Optional[str]
    duration: int
    #  path: List[Instruction]
    geojson: dict

    def as_api_route_leg(self) -> RouteLeg:
        #  steps = []
        #  prev_coord = Coordinate(self.geojson["coordinates"]["0"])
        #
        #  for [lon,lat] in geojson['coordinates']:
        #      step = inst.as_api_route_step(prev_coord)
        #      prev_coord = inst.instruction_start_coordinate
        #      steps.append(RouteStep(
        #
        #          ))

        return RouteLeg(
            duration=self.duration,
            summary="todo",
            steps=[
                RouteStep(
                    maneuver=RouteManeuver(instruction="todo", location=(0, 0)),
                    duration=self.duration,
                    distance=42,
                    mode=TransportMode.bike,
                    geometry=self.geojson,
                )
            ],
        )


class Journey(BaseModel):
    arrival_date_time: datetime
    departure_date_time: datetime
    duration: int
    distances: Distances
    sections: List[Section]

    @validator("arrival_date_time", "departure_date_time", pre=True)
    def parse_date(cls, v):
        return datetime.strptime(v, "%Y%m%dT%H%M%S")

    def as_api_route(self) -> DirectionsRoute:
        return DirectionsRoute(
            duration=self.duration,
            distance=self.distances.overall(),
            start_time=datetime.isoformat(self.departure_date_time),
            end_time=datetime.isoformat(self.arrival_date_time),
            legs=[sec.as_api_route_leg() for sec in self.sections],
        )


class NavitiaResponse(BaseModel):
    journeys: List[Journey]

    def as_api_response(self) -> DirectionsResponse:
        return DirectionsResponse(
            status="ok",  # TODO,
            data=DirectionsData(routes=[journey.as_api_route() for journey in self.journeys]),
        )


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

    def directions_navitia(self, start, end, mode, lang, extra=None):
        url = settings["NAVITIA_API_BASE_URL"]
        start = start.get_coord()
        end = end.get_coord()

        print({"Authorization": settings["NAVITIA_API_TOKEN"]})

        params = {
            "from": f"{start['lon']};{start['lat']}",
            "to": f"{end['lon']};{end['lat']}",
            "direct_path_mode[]": mode,
        }

        response = self.session.get(
            url,
            params=params,
            headers={"Authorization": settings["NAVITIA_API_TOKEN"]},
        )

        response.raise_for_status()
        print(response.json())
        return NavitiaResponse(**response.json())

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

        res = self.directions_navitia(from_place, to_place, "bike", lang)
        print(res)
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
