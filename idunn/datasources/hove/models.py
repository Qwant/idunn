"""
Derialize Hove's responses and conversion primitives following the following equivalence:
 - route <-> journey
 - leg <-> section
 - step <-> single element of section ? Can be re-cut later ?
"""

import logging
from datetime import datetime
from typing import Iterator, List, Optional, Tuple

from geojson_pydantic.geometries import Geometry, LineString
from geojson_pydantic.types import Position
from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic import BaseModel

import idunn.directions.models as api
from idunn.directions.models import IdunnTransportMode

logger = logging.getLogger(__name__)


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

    def get_api_modifier(self) -> str:
        # See https://docs.api.com/api/navigation/directions/#step-maneuver-object
        mapping = [
            (-135, "sharp left"),
            (-90, "left"),
            (-45, "slight left"),
            (0, "straight"),
            (45, "slight right"),
            (90, "right"),
            (135, "sharp right"),
            (180, "uturn"),
        ]

        _, closest = min(
            (
                min(abs(self.direction - angle), abs(360 - self.direction - angle)),
                modifier,
            )
            for angle, modifier in mapping
        )

        return closest


class DisplayInformations(BaseModel):
    code: Optional[str]
    label: Optional[str]
    color: Optional[str]
    text_color: Optional[str]  # TODO: would be great to include in result
    network: Optional[str]
    direction: Optional[str]
    physical_mode: Optional[str]

    def as_api_transport_info(self) -> api.TransportInfo:
        return api.TransportInfo(
            num=self.code or self.label,
            direction=self.direction,
            lineColor=self.color,
            lineTextColor=self.text_color,
            network=self.network,
        )


class Section(BaseModel):
    sec_type: str = Field(..., alias="type")  # TODO: could be an enum
    mode: Optional[IdunnTransportMode]
    duration: int
    path: List[Instruction] = []
    geojson: Optional[Geometry]  # TODO: always set when not waiting
    display_informations: Optional[DisplayInformations]

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

    def get_api_mode(self) -> api.TransportMode:
        if self.mode:
            return self.mode.to_mapbox()

        # TODO: should we just return the api-provided name?
        if self.display_informations:
            match self.display_informations.physical_mode:
                case "Métro":
                    return api.TransportMode.subway
                case "RER":
                    return api.TransportMode.suburban_train
                case "Train Transilien":
                    return api.TransportMode.train
                case "Bus":
                    return api.TransportMode.bus
                case "Tramway":
                    return api.TransportMode.tram
                case other:
                    logger.warning("Unknown physical mode '%s'", other)

        return api.TransportMode.walk

    def as_api_route_summary_part(self) -> api.RouteSummaryPart:
        return api.RouteSummaryPart(
            mode=self.get_api_mode(),
            info=(
                self.display_informations.as_api_transport_info()
                if self.display_informations
                else None
            ),
            distance=42,
            duration=self.duration,
        )

    def as_api_route_leg(self) -> api.RouteLeg:
        default_location = (0, 0)  # TODO
        insts = list(self.cut_linestring())
        mode = self.get_api_mode()

        if not insts:
            steps = [
                api.RouteStep(
                    maneuver=api.RouteManeuver(
                        instruction="no instruction", location=default_location
                    ),
                    duration=self.duration,
                    distance=sum(inst.length for inst in self.path),
                    geometry=self.geojson.dict(),
                    properties={"mode": self.mode.value if self.mode else "tram"},
                    mode=mode,
                )
            ]
        else:
            steps = [
                api.RouteStep(
                    maneuver=api.RouteManeuver(
                        location=inst.instruction_start_coordinate.to_position(),
                        instruction=inst.instruction or inst.name,
                        modifier=inst.get_api_modifier(),
                    ),
                    duration=inst.duration,
                    distance=inst.length,
                    geometry=geo,
                    properties={"mode": self.mode.value if self.mode else "tram"},
                    mode=mode,
                )
                for (inst, geo) in insts
            ]

        return api.RouteLeg(
            duration=self.duration,
            distance=sum(step.distance for step in steps),
            summary="todo",
            steps=steps,
            info=(
                self.display_informations.as_api_transport_info()
                if self.display_informations
                else None
            ),
            to=api.TransportStop(location=self.geojson.coordinates[-1]),
            **{"from": api.TransportStop(location=self.geojson.coordinates[0])},
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

    def as_api_route(self) -> api.DirectionsRoute:
        secs = [sec for sec in self.sections if sec.sec_type != "waiting"]
        legs = [sec.as_api_route_leg() for sec in secs]

        return api.DirectionsRoute(
            duration=self.duration,
            distance=self.distances.overall(),
            start_time=datetime.isoformat(self.departure_date_time),
            end_time=datetime.isoformat(self.arrival_date_time),
            legs=legs,
            geometry={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "mode": leg.mode.value,
                            **(
                                {"lineColor": sec.display_informations.color}
                                if sec.display_informations
                                else {}
                            ),
                        },
                        "geometry": {
                            "type": "MultiLineString",
                            "coordinates": [step.geometry["coordinates"] for step in leg.steps],
                        },
                    }
                    for sec, leg in zip(secs, legs)
                    for step in leg.steps
                ],
            },
            summary=[
                summary
                for sec in self.sections
                if (summary := sec.as_api_route_summary_part()).info is not None
            ],
        )


class HoveResponse(BaseModel):
    journeys: List[Journey] = []

    def as_api_response(self) -> api.DirectionsResponse:
        return api.DirectionsResponse(
            status="ok",  # TODO,
            data=api.DirectionsData(routes=[journey.as_api_route() for journey in self.journeys]),
        )
