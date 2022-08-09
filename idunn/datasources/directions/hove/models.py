"""
Derialize Hove's responses and conversion primitives following the next equivalence:
 - route <-> journey
 - leg <-> section
 - step <-> single element of section ? Can be re-cut later ?
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Iterator, List, Optional, Tuple

from geojson_pydantic.geometries import Geometry, LineString
from geojson_pydantic.types import Position
from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic import BaseModel

import idunn.datasources.directions.mapbox.models as api
from idunn.datasources.directions.mapbox.models import IdunnTransportMode

logger = logging.getLogger(__name__)

# Precision considered in coordinates when cutting linestrings at stop positions.
# The error margin in meters that it corresponds to is at most:
#   40e6 * 1e-6 / 180 ~= 0.22m (considering the equator is 40e6 meters long)
COORD_PRECISION = 1e-6


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

    def get_api_modifier(self) -> api.ManeuverModifier:
        # Get the best modifier value that fits with the angle. For example, an
        # angle of 40° is a slight right turn and -130° would be a sharp left turn.
        #
        # See https://docs.mapbox.com/api/navigation/directions/#step-maneuver-object

        return min(
            list(api.ManeuverModifier),
            key=lambda modifier: min(
                abs(self.direction - modifier.angle),
                abs(360 - self.direction - modifier.angle),
            ),
        )


class DisplayInformations(BaseModel):
    code: Optional[str]
    label: Optional[str]
    color: Optional[str]
    text_color: Optional[str]
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


class StopPoint(BaseModel):
    id: str
    name: str
    coord: Coordinate


class StopDateTime(BaseModel):
    stop_point: StopPoint


class SectionType(Enum):
    PUBLIC_TRANSPORT = "public_transport"
    STREET_NETWORK = "street_network"
    WAITING = "waiting"
    STAY_IN = "stay_in"
    TRANSFER = "transfer"
    CROW_FLY = "crow_fly"
    ON_DEMAND_TRANSPORT = "on_demand_transport"
    BSS_RENT = "bss_rent"
    BSS_PUT_BACK = "bss_put_back"
    BOARDING = "boarding"
    LANDING = "landing"
    ALIGHTING = "alighting"
    PARK = "park"
    RIDESHARING = "ridesharing"


class LineStringExtProperties(BaseModel):
    length: int


class LineStringExt(LineString):
    """
    Extend linestring with extra properties.
    """

    properties: List[LineStringExtProperties]

    def as_linestring(self) -> LineString:
        return LineString(coordinates=self.coordinates)


class Section(BaseModel):
    sec_type: SectionType = Field(..., alias="type")
    mode: Optional[IdunnTransportMode]
    duration: int
    path: List[Instruction] = []
    geojson: Optional[LineStringExt]  # NOTE: this is always set when not waiting
    display_informations: Optional[DisplayInformations]
    stop_date_times: List[StopDateTime] = []

    @validator("mode", pre=True)
    def mode_from_navitia(cls, v):
        return IdunnTransportMode.parse(v)

    def cut_linestring(self) -> Iterator[Tuple[Instruction, Geometry]]:
        """
        Split path geometry at each instruction and wrap them together
        """
        all_coords = self.geojson.coordinates
        last_inst = None

        for inst in self.path:
            if not inst.instruction_start_coordinate:
                if last_inst is not None:
                    yield (last_inst, self.geojson.as_linestring())

                last_inst = inst
                continue

            end_coord = inst.instruction_start_coordinate.to_position()

            if last_inst is not None:
                try:
                    end_index = next(
                        i
                        for i, coord in enumerate(all_coords)
                        if abs(coord[0] - end_coord[0]) < COORD_PRECISION
                        and abs(coord[1] - end_coord[1]) < COORD_PRECISION
                    )

                    geometry = LineString(coordinates=all_coords[: end_index + 1])
                    all_coords = all_coords[end_index:]
                except StopIteration:
                    geometry = self.geojson.as_linestring()

                yield (last_inst, geometry)

            last_inst = inst

        if last_inst is not None:
            if len(all_coords) >= 2:
                geometry = LineString(coordinates=all_coords)
            else:
                geometry = self.geojson.as_linestring()

            yield (last_inst, geometry)

    def get_api_mode(self) -> api.TransportMode:
        if self.mode:
            return self.mode.to_mapbox()

        # TODO: should we just return the api-provided name?
        if self.display_informations:
            match self.display_informations.physical_mode:
                case "Subway" | "Metro" | "Métro":
                    return api.TransportMode.subway
                case "RER":
                    return api.TransportMode.suburban_train
                case "Train" | "Train Transilien":
                    return api.TransportMode.train
                case "Bus":
                    return api.TransportMode.bus_city
                case "Tramway":
                    return api.TransportMode.tram
                case other:
                    logger.warning("Unknown physical mode '%s'", other)
                    return api.TransportMode.train

        return api.TransportMode.walk

    def as_api_route_summary_part(self) -> api.RouteSummaryPart:
        return api.RouteSummaryPart(
            mode=self.get_api_mode(),
            info=(
                self.display_informations.as_api_transport_info()
                if self.display_informations
                else None
            ),
            distance=(
                self.geojson.properties[0].length
                if self.geojson
                else sum(inst.length for inst in self.path)
            ),
            duration=self.duration,
        )

    def as_api_route_leg(self) -> api.RouteLeg:
        default_location = self.geojson.coordinates[0][::-1]  # assuming this is a LineString
        insts = list(self.cut_linestring())
        mode = self.get_api_mode()

        stops = [
            api.TransportStop(
                id=dt.stop_point.id,
                name=dt.stop_point.name,
                location=(dt.stop_point.coord.lon, dt.stop_point.coord.lat),
            )
            for dt in self.stop_date_times
        ]

        if not insts:
            steps = [
                api.RouteStep(
                    maneuver=api.RouteManeuver(
                        instruction="no instruction",
                        location=default_location,
                    ),
                    duration=self.duration,
                    distance=self.geojson.properties[0].length,
                    geometry=self.geojson.as_linestring(),
                    properties={"mode": self.mode.value if self.mode else "tram"},
                    mode=mode,
                )
            ]

            summary = ""
        else:
            steps = [
                api.RouteStep(
                    maneuver=api.RouteManeuver(
                        location=(
                            inst.instruction_start_coordinate.to_position()
                            if inst.instruction_start_coordinate
                            else self.geojson.coordinates[0]
                        ),
                        instruction=inst.instruction or "",
                        modifier=inst.get_api_modifier(),
                        detail=api.ManeuverDetail(
                            name=inst.name,
                            direction=inst.direction,
                            duration=inst.duration,
                            length=inst.length,
                        ),
                    ),
                    duration=inst.duration,
                    distance=inst.length,
                    geometry=geo,
                    properties={"mode": self.mode.value if self.mode else "tram"},
                    mode=mode,
                )
                for (inst, geo) in insts
                if inst.name or inst.length != 0
            ]

            _, summary = max((step.distance, step.maneuver.detail.name) for step in steps)

        return api.RouteLeg(
            duration=self.duration,
            distance=self.geojson.properties[0].length,
            summary=summary,
            steps=steps,
            info=(
                self.display_informations.as_api_transport_info()
                if self.display_informations
                else None
            ),
            **(
                {
                    "from": stops[0],
                    "stops": stops[1:-1],
                    "to": stops[-1],
                }
                if stops
                else {}
            ),
        )


class FareTotal(BaseModel):
    currency: str = ""
    value: float


class Fare(BaseModel):
    found: bool
    total: Optional[FareTotal]

    def as_api_price(self) -> Optional[api.RoutePrice]:
        if not self.total:
            return None

        return api.RoutePrice(
            currency=self.total.currency,
            value=f"{self.total.value:.2f}",
        )


class CarbonEmissions(BaseModel):
    unit: str
    value: float

    def as_gec(self) -> Optional[float]:
        match self.unit:
            case "gEC":
                return self.value
            case "":
                pass
            case _:
                logger.warning("Only supported carbon unit is gEC, got %s", self.unit)

        return None


class Journey(BaseModel):
    arrival_date_time: datetime
    departure_date_time: datetime
    duration: int
    fare: Fare
    co2_emission: CarbonEmissions
    distances: Distances
    sections: List[Section]

    @validator("arrival_date_time", "departure_date_time", pre=True)
    def parse_date(cls, v):
        return datetime.strptime(v, "%Y%m%dT%H%M%S")

    def as_api_route(self) -> api.DirectionsRoute:
        secs = [sec for sec in self.sections if sec.sec_type != SectionType.WAITING]
        legs = [sec.as_api_route_leg() for sec in secs]
        summary = [sec.as_api_route_summary_part() for sec in secs]

        geometry = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "mode": leg.mode.value,
                        **(
                            {
                                "lineColor": sec.display_informations.color,
                                "lineTextColor": sec.display_informations.text_color,
                            }
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
            ],
        }

        return api.DirectionsRoute(
            distance=self.distances.overall(),
            duration=self.duration,
            carbon=self.co2_emission.as_gec(),
            price=self.fare.as_api_price(),
            start_time=datetime.isoformat(self.departure_date_time),
            end_time=datetime.isoformat(self.arrival_date_time),
            legs=legs,
            geometry=geometry,
            summary=summary,
        )


class HoveResponse(BaseModel):
    journeys: List[Journey] = []

    def as_api_response(self) -> api.DirectionsResponse:
        return api.DirectionsResponse(
            status="success",
            data=api.DirectionsData(routes=[journey.as_api_route() for journey in self.journeys]),
        )
