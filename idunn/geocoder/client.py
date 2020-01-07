import requests

from idunn import settings


class GeocoderClient:
    def __init__(self):
        self.session = requests.Session()

    def autocomplete(self, query, lang, limit, lon=None, lat=None, shape=None):
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

        # Call Bragi
        url = settings['BRAGI_BASE_URL'] + '/autocomplete'

        if shape:
            response = self.session.post(
                url,
                params=params,
                json={'shape': shape}
            )
        else:
            response = self.session.get(url, params=params)

        response.raise_for_status() # TODO: catch errors in [400, 500[
        return response.json()


geocoder_client = GeocoderClient()
