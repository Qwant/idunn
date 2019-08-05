from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Schema, validator


class TransportMode(str, Enum):
    walk = 'WALK'
    bicycle = 'BICYCLE'
    car = 'CAR'
    boat = 'BOAT'
    plane = 'PLANE'
    train = 'TRAIN'
    carpool = 'CARPOOL'
    bus = 'BUS'
    bus_city = 'BUS_CITY'
    vtc = 'VTC'
    taxi = 'TAXI'
    bike = 'BIKE'
    tram = 'TRAM'
    car_rental = 'CAR_RENTAL'
    transfert = 'TRANSFERT'
    subway = 'SUBWAY'
    suburban_train = 'SUBURBAN_TRAIN'
    seaplane = 'SEAPLANE'
    helicopter = 'HELICOPTER'
    funicular = 'FUNICULAR'
    shuttle = 'SHUTTLE'
    unknown = 'UNKNOW'
    wait = 'WAIT'


class RouteManeuver(BaseModel):
    location: Tuple[float, float] = Schema(..., description='[lon, lat]')
    modifier: Optional[str]
    type: str = ""
    instruction: str


class TransportInfo(BaseModel):
    num: str
    direction: str
    lineColor: str
    network: str


class TransportStop(BaseModel):
    name: str
    location: Tuple[float, float] = Schema(..., description='[lon, lat]')

    def __init__(self, **data):
        if 'stop' in data:
            data = data['stop']
        if 'location' not in data:
            if 'lng' in data and 'lat' in data:
                data['location'] = (data['lng'], data['lat'])
        super().__init__(**data)


class RouteStep(BaseModel):
    maneuver: RouteManeuver
    duration: float
    distance: float
    geometry: dict = Schema(..., description='GeoJSON')
    mode: TransportMode
    info: Optional[TransportInfo]
    stops: List[TransportStop] = []

    def __init__(self, **data):
        if 'shapes' in data:
            data['geometry'] = {
                'coordinates': data['shapes'],
                'type': 'LineString'
            }
        if 'type' in data:
            data['mode'] = data.pop('type')
        if data.get('infos'):
            data['info'] = data.pop('infos')
        if 'maneuver' not in data:
            from_object = data.get('from', {})
            data['maneuver'] = {
                'location': (from_object.get('lng'), from_object.get('lat')),
                'type': data.get('info', {}).pop('maneuverType', ''),
                'modifier': data.get('info', {}).pop('maneuverAction', None),
                'instruction': data.get('action', '')
            }
        super().__init__(**data)

    @validator('mode', pre=True)
    def transform_mode(cls, value):
        return {
            'cycling': TransportMode.bicycle,
            'driving': TransportMode.car,
            'ferry': TransportMode.boat,
            'walking': TransportMode.walk,
            'pushing bike': TransportMode.walk,
            'train': TransportMode.train,
            'unaccessible': TransportMode.unknown
        }.get(value) or value

    @validator('info', pre=True)
    def ignore_empty_info(cls, value):
        if not value:
            return None
        return value


class RouteLeg(BaseModel):
    duration: float = Schema(..., description='duration in seconds')
    distance: Optional[float] = Schema(..., description='distance in meters')
    summary: str
    steps: List[RouteStep]


class RouteSummaryPart(BaseModel):
    mode: TransportMode
    info: Optional[TransportInfo]
    distance: float = Schema(..., description='distance in meters')
    duration: float = Schema(..., description='duration in seconds')

    def __init__(self, **data):
        if 'type' in data:
            data['mode'] = data.pop('type')
        if data.get('infos'):
            data['info'] = data.pop('infos')
        super().__init__(**data)


class RoutePrice(BaseModel):
    currency: str
    value: str
    group: bool = False


class DirectionsRoute(BaseModel):
    duration: float = Schema(..., description='duration in seconds')
    distance: Optional[float] = Schema(..., description='distance in meters')
    carbon: Optional[float] = Schema(..., description='value in gEC')
    summary: Optional[List[RouteSummaryPart]]
    price: Optional[RoutePrice]
    legs: List[RouteLeg]
    geometry: dict = Schema({}, description='GeoJSON')

    def __init__(self, **data):
        if len(data.get('legs', [])) > 0:
            if 'steps' not in data['legs'][0]:
                data['legs'] = [
                    {
                        'duration': data.get('duration'),
                        'distance': data.get('distance'),
                        'steps': data['legs'],
                        'summary': data.get('id')
                    }
                ]
        if 'price' in data and data.get('price', {}).get('value') is None:
            data.pop('price')
        super().__init__(**data)

    @validator('geometry', always=True)
    def build_geometry(cls, geometry, values):
        if geometry:
            return geometry
        # geometry is not defined in raw response
        # Let's collect geometries from inner steps
        features_list = []
        for leg in values.get('legs', []):
            for step in leg.steps:
                feature = {
                    'type': 'Feature',
                    'geometry': step.geometry,
                    'properties': {
                        'mode': step.mode
                    }
                }
                if step.info:
                    feature['properties'].update(step.info)
                features_list.append(feature)
        return {
            'type': 'FeatureCollection',
            'features': features_list
        }


class DirectionsData(BaseModel):
    routes: List[DirectionsRoute]
    message: Optional[str] # in case of errors
    code: Optional[str]  # in case of errors

    def __init__(self, **data):
        if 'results' in data:
            data['routes'] = data.pop('results')
        super().__init__(**data)


class DirectionsResponse(BaseModel):
    status: str
    data: DirectionsData
