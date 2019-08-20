import requests
import logging
from idunn import settings
from datetime import datetime, timedelta
from .models import DirectionsResponse
from apistar.http import JSONResponse
from apistar.exceptions import BadRequest, HTTPException

logger = logging.getLogger(__name__)


class DirectionsClient:
    def __init__(self):
        self.qw_session = requests.Session()
        self.qw_session.headers['User-Agent'] = settings['USER_AGENT']

        self.combigo_session = requests.Session()
        self.combigo_session.headers['x-api-key'] = settings['COMBIGO_API_KEY']
        self.combigo_session.headers['User-Agent'] = settings['USER_AGENT']

    @property
    def QWANT_BASE_URL(self):
        return settings['QWANT_DIRECTIONS_API_BASE_URL']

    @property
    def COMBIGO_BASE_URL(self):
        return settings['COMBIGO_API_BASE_URL']

    def directions_qwant(self, start, end, mode, lang, extra=None):
        if not self.QWANT_BASE_URL:
            raise HTTPException(f"Directions API is currently unavailable for mode {mode}", status_code=501)

        if extra is None:
            extra = {}
        start_lon, start_lat = start
        end_lon, end_lat = end
        response = self.qw_session.get(
            f'{self.QWANT_BASE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}',
            params={
                'type': mode,
                'language': lang,
                'steps': 'true',
                'alternatives': 'true',
                'overview': 'full',
                'geometries': 'geojson',
                **extra
            }
        )

        if 400 <= response.status_code < 500:
            # Proxy client errors
            return JSONResponse(
                response.json(),
                status_code=response.status_code,
            )
        response.raise_for_status()
        return DirectionsResponse(**response.json()).dict()

    def directions_combigo(self, start, end, mode, lang, **kwargs):
        if not self.COMBIGO_BASE_URL:
            raise HTTPException(f"Directions API is currently unavailable for mode {mode}", status_code=501)

        start_lon, start_lat = start
        end_lon, end_lat = end
        response = self.combigo_session.get(
            f'{self.COMBIGO_BASE_URL}/journey/{start_lat};{start_lon}/{end_lat};{end_lon}',
            params={
                'lang': lang,
                'type_include': mode,
                'dTime': (datetime.utcnow() + timedelta(minutes=1)).isoformat(timespec='seconds')
            }
        )
        response.raise_for_status()

        return DirectionsResponse(
            status='success',
            data=response.json()
        ).dict()

    def get_directions(self, from_loc, to_loc, mode, lang, **extra):
        if mode in ('driving-traffic', 'driving', 'car'):
            method = self.directions_qwant
            mode = 'driving-traffic'
        elif mode in ('cycling',):
            method = self.directions_qwant
            mode = 'cycling'
        elif mode in ('walking', 'walk'):
            method = self.directions_qwant
            mode = 'walking'
        elif mode in ('publictransport', 'taxi', 'vtc', 'carpool'):
            method = self.directions_combigo
            mode = mode
        else:
            raise BadRequest(f'unknown mode {mode}')

        return method(from_loc, to_loc, mode, lang, **extra)


directions_client = DirectionsClient()
