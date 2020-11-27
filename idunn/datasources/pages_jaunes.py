from os import path
from typing import List

import requests
import logging
from elasticsearch import Elasticsearch
from fastapi import HTTPException

from idunn import settings
from idunn.places import PjApiPOI, PjPOI
from idunn.places.models import pj_info, pj_find
from idunn.utils.auth_session import AuthSession
from idunn.utils.geometry import bbox_inside_polygon, france_polygon

logger = logging.getLogger(__name__)


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


class PjAuthSession(AuthSession):
    def get_authorization_url(self):
        return "https://api.pagesjaunes.fr/oauth/client_credential/accesstoken"

    def get_authorization_params(self):
        return {
            "grant_type": "client_credentials",
            "client_id": settings.get("PJ_API_ID"),
            "client_secret": settings.get("PJ_API_SECRET"),
        }


class ApiPjSource(PjSource):
    PJ_RESULT_MAX_SIZE = 30
    PJ_INFO_API_URL = "https://api.pagesjaunes.fr/v1/pros"
    PJ_FIND_API_URL = "https://api.pagesjaunes.fr/v1/pros/search"

    def __init__(self):
        self.enabled = True
        self.session = PjAuthSession()

    @staticmethod
    def format_where(bbox):
        left, bot, right, top = bbox
        return f"gZ{left},{top},{right},{bot}"

    def get_from_params(self, url, params=None) -> PjApiPOI:
        res = self.session.get(url, params=params)
        res.raise_for_status()
        return res.json()

    def get_places_from_url(self, url, params=None, size=10):
        res = pj_find.Response(**self.get_from_params(url, params))
        pois = [PjApiPOI(listing) for listing in res.search_results.listings[:size] or []]

        if (
            len(pois) < size
            and res.context
            and res.context.pages
            and res.context.pages.next_page_url
        ):
            pois += self.get_places_from_url(
                res.context.pages.next_page_url.replace("/pros/find", "/pros/search"),
                size=size - len(pois),
            )

        return pois

    def get_places_bbox(self, raw_categories, bbox, size=10, query="") -> List[PjApiPOI]:
        query_params = {
            "what": " ".join(raw_categories),
            "where": self.format_where(bbox),
            "max": min(self.PJ_RESULT_MAX_SIZE, size),
        }

        if query:
            query_params["what"] += " " + query

        return self.get_places_from_url(self.PJ_FIND_API_URL, query_params, size)

    def get_place(self, poi_id) -> PjApiPOI:
        return PjApiPOI(
            pj_info.Response(
                **self.get_from_params(path.join(self.PJ_INFO_API_URL, self.internal_id(poi_id)))
            )
        )


pj_source = ApiPjSource() if settings.get("PJ_API_ID") else LegacyPjSource()
