import logging
import requests
from fastapi import HTTPException
from json.decoder import JSONDecodeError

from idunn import settings


logger = logging.getLogger(__name__)


class GeocoderClient:
    def __init__(self):
        self.session = requests.Session()

    @staticmethod
    def build_params(query, lang, limit, lon=None, lat=None):
        params = {
            'q': query,
            'lang': lang,
            'limit': limit,
        }

        if lon and lat:
            params.update({
                'lon': lon,
                'lat': lat,
            })

        return params

    def autocomplete(self, query, lang, limit, lon=None, lat=None, shape=None):
        params = GeocoderClient.build_params(query, lang, limit, lon, lat)
        url = settings['BRAGI_BASE_URL'] + '/autocomplete'

        if shape:
            response = self.session.post(
                url,
                params=params,
                json={'shape': shape},
            )
        else:
            response = self.session.get(url, params=params)

        if response.status_code != requests.codes.ok:
            try:
                explain = response.json()['long']
            except (IndexError, JSONDecodeError):
                explain = 'unknown reason'

            logger.error(
                'Request to Bragi returned with unexpected status %d: "%s"',
                response.status_code,
                explain,
            )
            raise HTTPException(500)

        return response.json()


geocoder_client = GeocoderClient()
