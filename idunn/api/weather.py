import requests
import logging
from apistar.exceptions import HTTPException

from idunn import settings
logger = logging.getLogger(__name__)



class WeatherClient:
    def __init__(self):
        self.session = requests.Session()
        self.request_timeout = float(settings['WEATHER_REQUEST_TIMEOUT'])

    @property
    def weather_url(self):
        return settings.get('WEATHER_API_URL')

    @property
    def weather_key(self):
        return settings.get('WEATHER_API_KEY')

    @property
    def enabled(self):
        return bool(self.weather_url and self.weather_key)

    def fetch_weather_places(self, coord) -> list:
        if not self.enabled:
            raise Exception('API is not enabled')

        url_weather_api = self.weather_url.format(lat=coord.get('lat'), lon=coord.get('lon'), appid=self.weather_key, lang="fr")

        weather_town = self.session.get(url_weather_api, timeout=self.request_timeout)
        weather_town.raise_for_status()
        try:
            weather_town = weather_town.json()
        except Exception:
            logger.error(f'Error with weather API JSON with request to {url_weather_api} '
                         f'Got {weather_town.content}', exc_info=True)
            raise HTTPException(detail='weather error', status_code=503)

        weather_info = { 'temperature': weather_town.get('main').get('temp'), 'weatherPic': weather_town.get('weather')[0].get('icon')}
        return weather_info


weather_client = WeatherClient()
