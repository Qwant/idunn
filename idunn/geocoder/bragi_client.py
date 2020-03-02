import logging
import requests
from json.decoder import JSONDecodeError

import pydantic
from fastapi import HTTPException

from idunn import settings
from .models import QueryParams, ExtraParams


logger = logging.getLogger(__name__)


class BragiClient:
    def __init__(self):
        self.session = requests.Session()
        if not settings["VERIFY_HTTPS"]:
            self.session.verify = False

    def autocomplete(self, query: QueryParams, extra: ExtraParams):
        params = query.bragi_query_dict()
        body = None
        if extra.shape:
            body = extra.dict()
        return self.raw_autocomplete(params, body)

    def raw_autocomplete(self, params, body=None):
        url = settings["BRAGI_BASE_URL"] + "/autocomplete"
        if body:
            response = self.session.post(url, params=params, json=body)
        else:
            response = self.session.get(url, params=params)

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
            return response.json()
        except (JSONDecodeError, pydantic.ValidationError) as e:
            logger.exception("Autocomplete invalid response")
            raise HTTPException(503, "Invalid response from the geocoder")


bragi_client = BragiClient()
