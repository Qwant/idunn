import logging
import requests
from json.decoder import JSONDecodeError

import pydantic
from fastapi import HTTPException

from idunn import settings
from .models import IdunnAutocomplete, QueryParams, ExtraParams, nlu_client


logger = logging.getLogger(__name__)


class GeocoderClient:
    def __init__(self):
        self.session = requests.Session()

    def autocomplete(self, query: QueryParams, extra: ExtraParams):
        if query.nlu:
            params = query.nlu_query_dict()
            intentions = nlu_client.get_intentions(params)

        url = settings["BRAGI_BASE_URL"] + "/autocomplete"
        params = query.bragi_query_dict()
        if extra.shape:
            response = self.session.post(url, params=params, json=extra.dict())
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
            results = response.json()
            if "intentions" in locals():
                results["intentions"] = intentions
            result_list = IdunnAutocomplete.parse_obj(results)
        except (JSONDecodeError, pydantic.ValidationError):
            raise HTTPException(503, "Invalid response from the geocoder")

        return result_list


geocoder_client = GeocoderClient()
