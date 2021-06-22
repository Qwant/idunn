from os import path
from typing import List

import logging
import requests
from elasticsearch import Elasticsearch
from fastapi import HTTPException
from requests import HTTPError as RequestsHTTPError

from idunn import settings
from idunn.places.pj_poi import PjApiPOI, PjPOI
from idunn.places.models import pj_info, pj_find
from idunn.places.exceptions import PlaceNotFound
from idunn.utils.auth_session import AuthSession
from idunn.utils.geometry import bbox_inside_polygon, france_polygon
from idunn.api.utils import CategoryEnum

logger = logging.getLogger(__name__)


class PjSource:
    PLACE_ID_NAMESPACE = "pj"

    def __init__(self):
        self.enabled = True

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

    # pylint: disable = unused-argument
    def search_places(self, query: str, place_in_query: bool, size=10) -> List[PjApiPOI]:
        logger.warning("calling unimplemented `search_places` with deprecated LegacyPjSource")
        return []

    def get_places_bbox(self, categories: List[CategoryEnum], bbox, size=10, query=""):
        raise NotImplementedError

    def get_place(self, poi_id):
        raise NotImplementedError


class LegacyPjSource(PjSource):
    es_index = settings.get("PJ_ES_INDEX")
    es_query_template = settings.get("PJ_ES_QUERY_TEMPLATE")

    def __init__(self):
        super().__init__()
        pj_es_url = settings.get("PJ_ES")

        if pj_es_url:
            self.es = Elasticsearch(pj_es_url, timeout=3.0)
            self.enabled = True
        else:
            self.enabled = False

    def get_places_bbox(self, categories: List[CategoryEnum], bbox, size=10, query=""):
        raw_categories = [pj_category for c in categories for pj_category in c.pj_filters()]
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
        # pylint: disable = unexpected-keyword-arg
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
    PJ_API_TIMEOUT = float(settings.get("PJ_API_TIMEOUT"))

    def __init__(self):
        super().__init__()
        self.session = PjAuthSession(refresh_timeout=self.PJ_API_TIMEOUT)

    @staticmethod
    def format_where(bbox):
        """
        >>> ApiPjSource.format_where([2e-5,-0.5,2,0.5])
        'gZ0.000020,-0.500000,2.000000,0.500000'

        """
        left, bot, right, top = bbox
        return f"gZ{left:.6f},{bot:.6f},{right:.6f},{top:.6f}"

    def get_from_params(self, url, params=None) -> PjApiPOI:
        res = self.session.get(url, params=params, timeout=self.PJ_API_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def get_places_from_url(self, url, params=None, size=10, ignore_status=()):
        try:
            res = pj_find.Response(**self.get_from_params(url, params))
        except requests.RequestException as exc:
            if exc.response is not None and exc.response.status_code in ignore_status:
                logger.debug("Ignored pagesjaunes error: %s", exc)
            else:
                logger.error("Failed to query pagesjaunes: %s", exc)
            return []

        pois = [PjApiPOI(listing) for listing in res.search_results.listings[:size] or []]

        if (
            len(pois) < size
            and res.context
            and res.context.pages
            and res.context.pages.next_page_url
        ):
            pois += self.get_places_from_url(
                res.context.pages.next_page_url,
                size=size - len(pois),
            )

        return pois

    def search_places(self, query: str, place_in_query: bool, size=10) -> List[PjApiPOI]:
        query_params = {"q": query if place_in_query else f"{query} france"}
        return self.get_places_from_url(
            self.PJ_FIND_API_URL, query_params, size, ignore_status=(400,)
        )

    def get_places_bbox(
        self, categories: List[CategoryEnum], bbox, size=10, query=""
    ) -> List[PjApiPOI]:
        query_params = {
            "what": " ".join(c.pj_what() for c in categories),
            "where": self.format_where(bbox),
            # The API may return less than 'max' items per page, so let's use 'size + 5'
            # as a margin to avoid requesting a second page unnecessarily.
            "max": min(self.PJ_RESULT_MAX_SIZE, size + 5),
        }

        if query:
            query_params["what"] += " " + query
            query_params["what"] = query_params["what"].strip()

        api_places = self.get_places_from_url(self.PJ_FIND_API_URL, query_params, size)

        # Remove null merchant ids
        # or duplicated merchant ids that may be returned in different pages
        merchant_ids = set()
        places = []
        for p in api_places:
            merchant_id = p.data.merchant_id
            if merchant_id and (merchant_id not in merchant_ids):
                places.append(p)
                merchant_ids.add(merchant_id)
        return places

    def get_place(self, poi_id) -> PjApiPOI:
        try:
            return PjApiPOI(
                pj_info.Response(
                    **self.get_from_params(
                        path.join(self.PJ_INFO_API_URL, self.internal_id(poi_id))
                    )
                )
            )
        except RequestsHTTPError as e:
            if e.response.status_code in (404, 400):
                logger.debug(
                    "Got HTTP %s from PagesJaunes API", e.response.status_code, exc_info=True
                )
                raise PlaceNotFound from e
            raise


pj_source = ApiPjSource() if settings.get("PJ_API_ID") else LegacyPjSource()
