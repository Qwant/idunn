import logging
import requests
from json.decoder import JSONDecodeError

import pydantic
from fastapi import HTTPException

from idunn import settings
from .models import GeocodeJson, QueryParams, ExtraParams


logger = logging.getLogger(__name__)


class GeocoderClient:
    def __init__(self):
        self.session = requests.Session()

    def autocomplete(self, query: QueryParams, extra: ExtraParams):
        url = settings["BRAGI_BASE_URL"] + "/autocomplete"

        if extra.shape:
            response = self.session.post(url, params=query.bragi_query_dict(), json=extra.dict())
        else:
            response = self.session.get(url, params=query.bragi_query_dict())

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

        try:
            results = GeocodeJson.parse_obj(response.json())
        except (JSONDecodeError, pydantic.ValidationError):
            raise HTTPException(503, "Invalid response from the geocoder")

        return results


geocoder_client = GeocoderClient()
