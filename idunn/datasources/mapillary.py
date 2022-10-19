import requests
import logging

from idunn import settings

logger = logging.getLogger(__name__)


class MapillaryClient:
    def __init__(self):
        self.session = requests.Session()
        self.request_timeout = float(settings["MAPILLARY_API_TIMEOUT"])

    @property
    def mapillary_api_url(self):
        return settings.get("MAPILLARY_API_URL")

    @property
    def mapillary_token(self):
        return settings.get("MAPILLARY_API_TOKEN")

    @property
    def enabled(self):
        return bool(self.mapillary_api_url and self.mapillary_token)

    def fetch_mapillary_place(self, image_id) -> str:
        if not self.enabled:
            return ""
        url = self.mapillary_api_url + image_id
        self.session.headers["Authorization"] = "OAuth " + self.mapillary_token
        params = {"fields": "thumb_1024_url"}
        response = self.session.get(
            url, params=params, timeout=settings.get("MAPILLARY_API_TIMEOUT")
        )
        try:
            thumb_1024_url = response.json()["thumb_1024_url"]
        except Exception as exc:
            logger.error(
                "Error with mapillary API JSON with request to ",
                url,
                exc_info=True,
            )
            return ""

        return thumb_1024_url


mapillary_client = MapillaryClient()
