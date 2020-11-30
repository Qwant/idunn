from typing import List

import requests
import logging
from elasticsearch import Elasticsearch
from fastapi import HTTPException
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from idunn import settings
from idunn.places import PjApiPOI, PjPOI
from idunn.places.models import pj_info, pj_find
from idunn.utils.geometry import bbox_inside_polygon, france_polygon

logger = logging.getLogger(__name__)

# TODO: add a shortcircuit mecanism in case PJ is not reliable?


class PjSource:
    PLACE_ID_NAMESPACE = "pj"

    def bbox_is_covered(self, bbox):
        if not self.enabled:
            return False
        return bbox_inside_polygon(*bbox, poly=france_polygon)

    def point_is_covered(self, point):
        if not self.enabled:
            return False
        return france_polygon.contains(point)

    def internal_id(self, poi_id):
        return poi_id.replace(f"{self.PLACE_ID_NAMESPACE}:", "", 1)

    def get_places_bbox(self, raw_categories, bbox, size=10, query=""):
        raise NotImplementedError

    def get_place(self, poi_id):
        raise NotImplementedError


class LegacyPjSource(PjSource):
    es_index = settings.get("PJ_ES_INDEX")
    es_query_template = settings.get("PJ_ES_QUERY_TEMPLATE")

    def __init__(self):
        pj_es_url = settings.get("PJ_ES")

        if pj_es_url:
            self.es = Elasticsearch(pj_es_url, timeout=3.0)
            self.enabled = True
        else:
            self.enabled = False

    def get_places_bbox(self, raw_categories, bbox, size=10, query=""):
        left, bot, right, top = bbox

        body = {
            "id": self.es_query_template,
            "params": {
                "query": query,
                "top_left_lat": top,
                "top_left_lon": left,
                "bottom_right_lat": bot,
                "bottom_right_lon": right,
            },
        }

        if query:
            body["params"]["match_amenities"] = True
        if raw_categories:
            body["params"]["filter_category"] = True
            body["params"]["category"] = raw_categories

        result = self.es.search_template(index=self.es_index, body=body, params={"size": size})
        raw_places = result.get("hits", {}).get("hits", [])
        return [PjPOI(p["_source"]) for p in raw_places]

    def get_place(self, poi_id):
        es_places = self.es.search(
            index=self.es_index,
            body={"query": {"bool": {"filter": {"term": {"_id": self.internal_id(poi_id)}}}}},
            ignore_unavailable=True,
        )

        es_place = es_places.get("hits", {}).get("hits", [])
        if len(es_place) == 0:
            raise HTTPException(status_code=404, detail=f"place {poi_id} not found")
        if len(es_place) > 1:
            logger.warning("Got multiple places with id %s", poi_id)
        return PjPOI(es_place[0]["_source"])


class ApiPjSource(PjSource):
    PJ_INFO_API_URL = "https://api.pagesjaunes.fr/v1/pros"
    PJ_FIND_API_URL = "https://api.pagesjaunes.fr/v1/pros/search"
    PJ_AUTHORIZATION = "https://api.pagesjaunes.fr/oauth/client_credential/accesstoken"

    def __init__(self):
        self.enabled = True
        self.client_id = settings.get("PJ_API_ID")
        self.client_secret = settings.get("PJ_API_SECRET")

        # TODO: refresh token if available?
        #       https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#refreshing-tokens
        self.client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=self.client)
        self.token = self.oauth.fetch_token(
            token_url=self.PJ_AUTHORIZATION,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    @staticmethod
    def format_where(bbox):
        left, bot, right, top = bbox
        return f"gZ{left},{top},{right},{bot}"

    # TODO: this requires a strong error management as it calls an external API
    def get_from_params(self, url, params) -> PjApiPOI:
        res = self.oauth.get(url, params=params)
        res.raise_for_status()
        return res.json()

    def get_places_bbox(self, raw_categories, bbox, size=10, query="") -> List[PjApiPOI]:
        query_params = {
            "what": raw_categories,
            "where": self.format_where(bbox),
            # TODO: add some scrolling mechanism, which should come with some async?
            "max": min(30, size),
        }

        if query:
            query_params["q"] = query

        res = pj_find.Response(**self.get_from_params(self.PJ_FIND_API_URL, query_params))

        if not res:
            return None

        return [PjApiPOI(listing) for listing in res.search_results.listings or []]

    def get_place(self, poi_id) -> PjApiPOI:
        return PjApiPOI(
            pj_info.Response(
                **self.get_from_params(
                    self.PJ_INFO_API_URL, {"listing_id": self.internal_id(poi_id)}
                )
            )
        )


pj_source = ApiPjSource() if settings.get("PJ_API_ID") else LegacyPjSource()
