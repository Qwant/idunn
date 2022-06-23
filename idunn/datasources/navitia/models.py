"""
Derialize Hove's responses and conversion primitives following the following equivalence:
 - route <-> journey
 - leg <-> section
 - step <-> single element of section ? Can be re-cut later ?
"""

from datetime import datetime
from typing import Iterator, List, Optional, Tuple

from geojson_pydantic.geometries import Geometry, LineString
from geojson_pydantic.types import Position
from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic import BaseModel

import idunn.directions.models as mapbox
from idunn.directions.models import IdunnTransportMode


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


class DisplayInformations(BaseModel):
    color: Optional[str]
    text_color: Optional[str]
    label: Optional[str]


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

    def as_api_route_leg(self) -> mapbox.RouteLeg:
        default_location = (0, 0)  # TODO
        insts = list(self.cut_linestring())

        if self.mode:
            mode = self.mode.to_mapbox()
        else:
            mode = mapbox.TransportMode.tram

        if not insts:
            steps = [
                mapbox.RouteStep(
                    maneuver=mapbox.RouteManeuver(
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
                mapbox.RouteStep(
                    maneuver=mapbox.RouteManeuver(
                        location=inst.instruction_start_coordinate.to_position(),
                        instruction=inst.instruction or inst.name,
                        modifier=inst.get_mapbox_modifier(),
                    ),
                    duration=inst.duration,
                    distance=inst.length,
                    geometry=geo,
                    properties={"mode": self.mode.value if self.mode else "tram"},
                    mode=mode,
                )
                for (inst, geo) in insts
            ]

        return mapbox.RouteLeg(
            duration=self.duration,
            summary="todo",
            steps=steps,
            from_=mapbox.TransportStop(location=self.geojson.coordinates[0]),
            to=mapbox.TransportStop(location=self.geojson.coordinates[-1]),
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

    def as_api_route(self) -> mapbox.DirectionsRoute:
        legs = [
            sec.as_api_route_leg()
            for sec in self.sections
            if sec.sec_type != "waiting" and sec.sec_type != "tram"
        ]

        return mapbox.DirectionsRoute(
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
                    for sec, leg in zip(self.sections, legs)
                    for step in leg.steps
                ],
            },
            summary=[
                mapbox.RouteSummaryPart(
                    mode=mapbox.TransportMode.bike,
                    info=mapbox.TransportInfo(
                        num="42",
                        direction="todo",
                        lineColor="ff0000",
                        network="RATP",
                    ),
                    distance=1337,
                    duration=42,
                ),
                mapbox.RouteSummaryPart(
                    mode=mapbox.TransportMode.walk,
                    info=None,
                    distance=1337,
                    duration=42,
                ),
                mapbox.RouteSummaryPart(
                    mode=mapbox.TransportMode.bike,
                    info=mapbox.TransportInfo(
                        num="0",
                        direction="todo",
                        lineColor="00ff00",
                        network="RATP",
                    ),
                    distance=1337,
                    duration=42,
                ),
            ],
        )


class NavitiaResponse(BaseModel):
    journeys: List[Journey] = []

    def as_api_response(self) -> mapbox.DirectionsResponse:
        return mapbox.DirectionsResponse(
            status="ok",  # TODO,
            data=mapbox.DirectionsData(
                routes=[journey.as_api_route() for journey in self.journeys]
            ),
        )
