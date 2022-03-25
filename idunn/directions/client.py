from copy import deepcopy
from enum import Enum
from geojson_pydantic.geometries import Geometry, LineString
from geojson_pydantic.types import Position
from pydantic.fields import Field
import requests
import logging
from datetime import datetime, timedelta
from starlette.requests import QueryParams
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Iterator, List, Optional, Tuple
from pydantic.class_validators import validator
from shapely.geometry import Point
from geojson_pydantic import Feature
from shapely.ops import unary_union, cascaded_union
from shapely.geometry import shape
import shapely.geometry


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
    TransportStop,
)

logger = logging.getLogger(__name__)

COMBIGO_SUPPORTED_LANGUAGES = {"en", "es", "de", "fr", "it"}


class IdunnTransportMode(Enum):
    CAR = "car"
    BIKE = "bike"
    WALKING = "walking"
    PUBLICTRANSPORT = "publictransport"

    @classmethod
    def parse(cls, mode: str):
        if mode in ("driving-traffic", "driving", "car", "car_no_park"):
            return cls.CAR
        if mode in ("cycling",):
            return cls.BIKE
        if mode in ("walking", "walk"):
            return cls.WALKING
        if mode in ("publictransport", "taxi", "vtc", "carpool"):
            return cls.PUBLICTRANSPORT

    def to_navitia(self) -> str:
        if self == self.CAR:
            return "car_no_park"
        return self.value

    def to_mapbox(self) -> TransportMode:
        # NOTE: switch to Python 3.10 for more eleguant matching ?
        if self == self.CAR:
            return TransportMode.car
        if self == self.BIKE:
            return TransportMode.bicycle
        if self == self.WALKING:
            return TransportMode.walk
        if self == self.PUBLICTRANSPORT:
            return TransportMode.tram


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

    def to_position(self) -> Position:
        return (self.lon, self.lat)


class Instruction(BaseModel):
    direction: int
    duration: int
    instruction: Optional[str]
    instruction_start_coordinate: Optional[Coordinate]
    length: int
    name: str

    def get_mapbox_modifier(self) -> str:
        # See https://docs.mapbox.com/api/navigation/directions/#step-maneuver-object
        mapping = {
            -135: "sharp left",
            -90: "left",
            -45: "slight left",
            0: "straight",
            45: "slight right",
            90: "right",
            135: "sharp right",
            180: "uturn",
        }

        closest = min(
            *mapping.keys(),
            key=lambda angle: min(abs(self.direction - angle), abs(360 - self.direction - angle)),
        )

        return mapping[closest]


class Section(BaseModel):
    sec_type: str = Field(..., alias="type")  # TODO: could be an enum
    mode: Optional[IdunnTransportMode]
    duration: int
    path: List[Instruction] = []
    geojson: Optional[Geometry]  # TODO: always set when not waiting

    @validator("mode", pre=True)
    def mode_from_navitia(cls, v):
        return IdunnTransportMode.parse(v)

    def cut_linestring(self) -> Iterator[Tuple[Instruction, Geometry]]:
        """
        Split path geometry at each instruction and wrap them together
        """
        all_coords = self.geojson.coordinates
        first_pass = True
        last_inst = None

        for inst in self.path:
            if not inst.instruction_start_coordinate:
                continue

            end_coord = inst.instruction_start_coordinate.to_position()

            try:
                end_index = next(
                    i
                    for i, coord in enumerate(all_coords)
                    if abs(coord[0] - end_coord[0]) < 1e-6 and abs(coord[1] - end_coord[1]) < 1e-6
                )
            except StopIteration:
                continue

            if first_pass:
                first_pass = False
                last_inst = inst
                continue

            yield (last_inst, LineString(coordinates=all_coords[: end_index + 1]))
            all_coords = all_coords[end_index:]
            last_inst = inst

        if last_inst and len(all_coords) >= 2:
            yield (last_inst, LineString(coordinates=all_coords))

    def as_api_route_leg(self) -> RouteLeg:
        default_location = (0, 0)  # TODO
        insts = list(self.cut_linestring())

        if self.mode:
            mode = self.mode.to_mapbox()
        else:
            mode = TransportMode.unknown

        if not insts:
            steps = [
                RouteStep(
                    maneuver=RouteManeuver(instruction="no instruction", location=default_location),
                    duration=self.duration,
                    distance=sum(inst.length for inst in self.path),
                    geometry=self.geojson.dict(),
                    mode=mode,
                )
            ]
        else:
            steps = [
                RouteStep(
                    maneuver=RouteManeuver(
                        location=inst.instruction_start_coordinate.to_position(),
                        instruction=inst.instruction or inst.name,
                        modifier=inst.get_mapbox_modifier(),
                    ),
                    duration=inst.duration,
                    distance=inst.length,
                    geometry=geo,
                    mode=mode,
                )
                for (inst, geo) in insts
            ]

        return RouteLeg(
            duration=self.duration,
            summary="todo",
            steps=steps,
            from_=TransportStop(location=self.geojson.coordinates[0]),
            to=TransportStop(location=self.geojson.coordinates[-1]),
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
        legs = [sec.as_api_route_leg() for sec in self.sections if sec.sec_type != "waiting"]

        return DirectionsRoute(
            duration=self.duration,
            distance=self.distances.overall(),
            start_time=datetime.isoformat(self.departure_date_time),
            end_time=datetime.isoformat(self.arrival_date_time),
            legs=legs,
            geometry=shapely.geometry.mapping(
                unary_union([shape(step.geometry) for leg in legs for step in leg.steps])
            ),
        )


class NavitiaResponse(BaseModel):
    journeys: List[Journey] = []

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

        self.combigo_session = requests.Session()
        self.combigo_session.headers["x-api-key"] = settings["COMBIGO_API_KEY"]
        self.combigo_session.headers["User-Agent"] = settings["USER_AGENT"]

        self.request_timeout = float(settings["DIRECTIONS_TIMEOUT"])

    @property
    def QWANT_BASE_URL(self):  # pylint: disable = invalid-name
        return settings["QWANT_DIRECTIONS_API_BASE_URL"]

    @property
    def COMBIGO_BASE_URL(self):  # pylint: disable = invalid-name
        return settings["COMBIGO_API_BASE_URL"]

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

    def directions_navitia(self, start, end, mode: IdunnTransportMode, lang, extra=None):
        url = settings["NAVITIA_API_BASE_URL"]
        start = start.get_coord()
        end = end.get_coord()

        params = {
            "from": f"{start['lon']};{start['lat']}",
            "to": f"{end['lon']};{end['lat']}",
            "direct_path_mode[]": mode.to_navitia(),
            "direct_path": "only",
            "free_radius_from": 50,
            "free_radius_to": 50,
            "max_walking_direct_path_duration": 86400,
            "max_bike_direct_path_duration": 86400,
            "max_car_no_park_direct_path_duration": 86400,
            "min_nb_journeys": 2,
            "max_nb_journeys": 5,
        }

        response = self.session.get(
            url,
            params=params,
            headers={"Authorization": settings["NAVITIA_API_TOKEN"]},
        )

        response.raise_for_status()
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
        if not DirectionsClient.is_in_allowed_zone(mode, from_place, to_place):
            raise HTTPException(
                status_code=422,
                detail="requested path is not inside an allowed area",
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
        else:
            raise HTTPException(status_code=400, detail=f"unknown mode {mode}")

        idunn_mode = IdunnTransportMode.parse(mode)
        res = self.directions_navitia(from_place, to_place, idunn_mode, lang)
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
