from datetime import datetime, timedelta
from enum import Enum
from functools import cached_property
from pydantic import BaseModel, Field, validator
from pytz import utc
from typing import List, Optional, Tuple


class TransportMode(str, Enum):
    walk = "WALK"
    bicycle = "BICYCLE"
    car = "CAR"
    boat = "BOAT"
    plane = "PLANE"
    train = "TRAIN"
    carpool = "CARPOOL"
    bus = "BUS"
    bus_city = "BUS_CITY"
    vtc = "VTC"
    taxi = "TAXI"
    bike = "BIKE"
    tram = "TRAM"
    car_rental = "CAR_RENTAL"
    transfert = "TRANSFERT"
    subway = "SUBWAY"
    suburban_train = "SUBURBAN_TRAIN"
    seaplane = "SEAPLANE"
    helicopter = "HELICOPTER"
    funicular = "FUNICULAR"
    shuttle = "SHUTTLE"
    unknown = "UNKNOW"  # sic, without 'N' as it is in Combigo docs (typo ?)
    wait = "WAIT"


class IdunnTransportMode(Enum):
    CAR = "car"
    BIKE = "bike"
    WALKING = "walking"
    PUBLICTRANSPORT = "publictransport"

    @classmethod
    def parse(cls, mode: str):
        match mode:
            case "driving-traffic" | "driving" | "car" | "car_no_park":
                return cls.CAR
            case "cycling":
                return cls.BIKE
            case "walking" | "walk":
                return cls.WALKING
            case "publictransport" | "taxi" | "vtc" | "carpool":
                return cls.PUBLICTRANSPORT

    def to_hove(self) -> str:
        if self == self.CAR:
            return "car_no_park"
        return self.value

    def to_mapbox(self) -> TransportMode:
        match self:
            case self.CAR:
                return TransportMode.car
            case self.BIKE:
                return TransportMode.bicycle
            case self.WALKING:
                return TransportMode.walk
            case self.PUBLICTRANSPORT:
                return TransportMode.tram

    def to_mapbox_query_param(self) -> str:
        match self:
            case self.CAR:
                return "driving-traffic"
            case self.BIKE:
                return "cycling"
            case self.WALKING:
                return "walking"
            case _:
                raise Exception(f"Invalid mode {self} for mapbox")


class ManeuverModifier(str, Enum):
    """
    See https://docs.mapbox.com/api/navigation/directions/#step-maneuver-object
    """

    SHARP_LEFT = "sharp left"
    LEFT = "left"
    SLIGHT_LEFT = "slight left"
    STRAIGHT = "straight"
    SLIGHT_RIGHT = "slight right"
    RIGHT = "right"
    SHARP_RIGHT = "sharp right"
    UTURN = "uturn"

    @cached_property
    def angle(self):
        match self:
            case self.SHARP_LEFT:
                return -135
            case self.LEFT:
                return -90
            case self.SLIGHT_LEFT:
                return -45
            case self.STRAIGHT:
                return 0
            case self.SLIGHT_RIGHT:
                return 45
            case self.RIGHT:
                return 90
            case self.SHARP_RIGHT:
                return 135
            case self.UTURN:
                return 180


class ManeuverDetail(BaseModel):
    """
    This is an extension to Mapbox's return format.
    """

    name: str
    direction: int = Field(description="Turn angle, Degrees")
    duration: int = Field(description="Seconds")
    length: int = Field(description="Meters")


class RouteManeuver(BaseModel):
    location: Tuple[float, float] = Field(..., description="[lon, lat]")
    modifier: Optional[ManeuverModifier]
    type: str = ""
    instruction: str
    detail: Optional[ManeuverDetail]  # extended from mapbox


class TransportInfo(BaseModel):
    num: Optional[str]
    direction: Optional[str]
    lineColor: Optional[str]
    lineTextColor: Optional[str]  # extended from mapbox
    network: Optional[str]

    def __init__(self, **data):
        if "transporterName" in data:
            data["network"] = data["transporterName"]
        super().__init__(**data)

    @validator("lineColor")
    def validate_color(cls, value):
        """
        >>> TransportInfo.validate_color("6eca97")
        '6eca97'
        >>> TransportInfo.validate_color("7852")
        '007852'
        >>> assert TransportInfo.validate_color("0123456") is None
        >>> assert TransportInfo.validate_color(None) is None
        """
        if not value or len(value) > 6:
            return None
        if len(value) < 6:
            return f"000000{value}"[-6:]
        return value


class TransportStop(BaseModel):
    id: Optional[str]
    name: Optional[str]
    location: Tuple[float, float] = Field(..., description="[lon, lat]")

    def __init__(self, **data):
        if "stop" in data:
            data = data["stop"]
        if "location" not in data:
            if "lng" in data and "lat" in data:
                data["location"] = (data["lng"], data["lat"])
        super().__init__(**data)


class RouteStep(BaseModel):
    maneuver: RouteManeuver
    duration: int
    distance: int
    geometry: dict = Field(..., description="GeoJSON")
    properties: dict = {}
    mode: TransportMode

    def __init__(self, **data):
        if "shapes" in data:
            data["geometry"] = {"coordinates": data["shapes"], "type": "LineString"}

        if "type" in data:
            data["mode"] = data.pop("type")

        if isinstance(data["maneuver"], dict):
            if "instruction" not in data["maneuver"]:
                data["maneuver"]["instruction"] = data.get("instruction")

            if "location" not in data["maneuver"]:
                if len(data.get("shapes", [])) > 0:
                    data["maneuver"]["location"] = tuple(data["shapes"][0])

        super().__init__(**data)

    @validator("mode", pre=True)
    def transform_mode(cls, value):
        return {
            "cycling": TransportMode.bicycle,
            "driving": TransportMode.car,
            "ferry": TransportMode.boat,
            "walking": TransportMode.walk,
            "pushing bike": TransportMode.walk,
            "train": TransportMode.train,
            "unaccessible": TransportMode.unknown,
        }.get(value) or value


class RouteLeg(BaseModel):
    duration: int = Field(..., description="duration in seconds")
    distance: Optional[int] = Field(None, description="distance in meters")
    summary: str
    steps: List[RouteStep] = []
    stops: List[TransportStop] = []
    info: Optional[TransportInfo]
    mode: TransportMode = TransportMode.unknown
    from_: Optional[TransportStop] = Field(None, alias="from")
    to: Optional[TransportStop]

    def __init__(self, **data):
        if data.get("infos"):
            data["info"] = data.pop("infos")
        if "summary" not in data:
            data["summary"] = data.get("id") or data.get("type")
        if "type" in data:
            leg_type = data["type"]
            data["mode"] = leg_type
            for s in data.get("steps", []):
                s["type"] = leg_type
        if "shapes" in data:
            for s in data.get("steps", []):
                if "beginShapeIndex" in s and "endShapeIndex" in s:
                    s["shapes"] = data["shapes"][s["beginShapeIndex"] : s["endShapeIndex"]]
        super().__init__(**data)

    @validator("info", pre=True)
    def ignore_empty_info(cls, value):
        if not value:
            return None
        return value

    @validator("mode", always=True)
    def build_mode(cls, mode, values):
        if mode != TransportMode.unknown:
            return mode
        modes = set(s.mode for s in values["steps"])
        if len(modes) == 1:
            return modes.pop()
        return TransportMode.unknown


class RouteSummaryPart(BaseModel):
    mode: TransportMode
    info: Optional[TransportInfo]
    distance: int = Field(..., description="distance in meters")
    duration: int = Field(..., description="duration in seconds")

    def __init__(self, **data):
        if "type" in data:
            data["mode"] = data.pop("type")
        if data.get("infos"):
            data["info"] = data.pop("infos")
        super().__init__(**data)


class RoutePrice(BaseModel):
    currency: str
    value: str = ""
    group: bool = False


class DirectionsRoute(BaseModel):
    duration: int = Field(..., description="duration in seconds")
    distance: Optional[int] = Field(None, description="distance in meters")
    carbon: Optional[float] = Field(None, description="value in gEC")
    summary: Optional[List[RouteSummaryPart]]
    price: Optional[RoutePrice]
    legs: List[RouteLeg]
    geometry: dict = Field({}, description="GeoJSON")
    start_time: str
    end_time: str

    @validator("price")
    def check_price(cls, v: Optional[RoutePrice]) -> Optional[RoutePrice]:
        if v and not v.value:
            return None

        return v

    def __init__(self, **data):
        context = data.get("context")

        if "geometry" not in data:
            features_list = []
            for idx, leg in enumerate(data["legs"]):
                if "shapes" in leg:
                    feature = {
                        "type": "Feature",
                        "geometry": {"coordinates": leg["shapes"], "type": "LineString"},
                        "properties": {"leg_index": idx, "mode": "WALK"},
                    }
                    features_list.append(feature)
            data["geometry"] = {"type": "FeatureCollection", "features": features_list}

        if "start_time" not in data or "end_time" not in data:
            if "dTime" in data and "aTime" in data:
                # Handle combigo's output format
                start = utc.localize(datetime.utcfromtimestamp(int(data["dTime"]) / 1000))
                end = utc.localize(datetime.utcfromtimestamp(int(data["aTime"]) / 1000))
            else:
                start = utc.localize(datetime.utcnow())
                end = start + timedelta(seconds=data.get("duration", 0))

            data["start_time"] = start.astimezone(context["start_tz"]).isoformat(timespec="seconds")
            data["end_time"] = end.astimezone(context["end_tz"]).isoformat(timespec="seconds")

        super().__init__(**data)

    def __eq__(self, other):
        return self.summary == other.summary

    @validator("geometry", always=True)
    def build_geometry(cls, geometry, values):
        if "legs" not in values:
            return geometry
        legs = values["legs"]
        for feature in geometry.get("features", []):
            leg_index = feature["properties"].get("leg_index")
            if leg_index is not None:
                leg = legs[leg_index]
                feature["properties"]["mode"] = leg.mode
                if leg.info:
                    feature["properties"].update(leg.info)
        return geometry


class DirectionsData(BaseModel):
    routes: List[DirectionsRoute]
    message: Optional[str]  # in case of errors
    code: Optional[str]  # in case of errors

    def __init__(self, **data):
        context = data.get("context")

        if "results" in data:
            # Handle combigo's output format
            data["routes"] = data.pop("results")

        for route in data["routes"]:
            if isinstance(route, dict):
                route["context"] = context

        super().__init__(**data)


class DirectionsResponse(BaseModel):
    status: str
    data: DirectionsData
