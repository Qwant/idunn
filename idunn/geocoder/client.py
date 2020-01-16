import logging
import requests
from fastapi import HTTPException
from json.decoder import JSONDecodeError

from idunn import settings
from .models import GeocodeJson, QueryParams, ExtraParams


logger = logging.getLogger(__name__)


class GeocoderClient:
    def __init__(self):
        self.session = requests.Session()

    def autocomplete(self, query: QueryParams, extra: ExtraParams):
        url = settings["BRAGI_BASE_URL"] + "/autocomplete"

        if extra.shape:
            response = self.session.post(url, params=query.dict(), json=extra.dict())
        else:
            response = self.session.get(url, params=query.dict())

        if response.status_code != requests.codes.ok:
            try:
                explain = response.json()["long"]
            except (IndexError, JSONDecodeError):
                explain = response.text

            logger.error(
                'Request to Bragi returned with unexpected status %d: "%s"',
                response.status_code,
                explain,
            )
            raise HTTPException(503, "Unexpected geocoder error")

        return GeocodeJson.parse_obj(response.json())


geocoder_client = GeocoderClient()
