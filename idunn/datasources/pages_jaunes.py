import logging
from os import path
from typing import List

import requests
from requests import HTTPError as RequestsHTTPError
from starlette.concurrency import run_in_threadpool

from idunn import settings
from idunn.datasources import Datasource
from idunn.geocoder.models.params import QueryParams
from idunn.places.exceptions import PlaceNotFound
from idunn.places.models import pj_info, pj_find
from idunn.places.pj_poi import PjApiPOI
from idunn.utils.auth_session import AuthSession
from idunn.utils.category import CategoryEnum
from idunn.utils.geometry import bbox_inside_polygon, france_polygon
from idunn.utils.result_filter import ResultFilter

logger = logging.getLogger(__name__)
result_filter = ResultFilter()


class PjAuthSession(AuthSession):
    def get_authorization_url(self):
        return "https://api.pagesjaunes.fr/oauth/client_credential/accesstoken"

    def get_authorization_params(self):
        return {
            "grant_type": "client_credentials",
            "client_id": settings.get("PJ_API_ID"),
            "client_secret": settings.get("PJ_API_SECRET"),
        }


class PagesJaunes(Datasource):
    PLACE_ID_NAMESPACE = "pj"
    PJ_RESULT_MAX_SIZE = 30
    PJ_INFO_API_URL = "https://api.pagesjaunes.fr/v1/pros"
    PJ_FIND_API_URL = "https://api.pagesjaunes.fr/v1/pros/search"
    PJ_API_TIMEOUT = float(settings.get("PJ_API_TIMEOUT"))

    def __init__(self):
        super().__init__()
        pj_api_url = settings.get("PJ_API_ID")
        if pj_api_url:
            self.session = PjAuthSession(refresh_timeout=self.PJ_API_TIMEOUT)
            self.enabled = True
        else:
            self.enabled = False

    @staticmethod
    def format_where(bbox):
        """
        >>> PagesJaunes.format_where([2e-5,-0.5,2,0.5])
        'gZ0.000020,-0.500000,2.000000,0.500000'

        """
        left, bot, right, top = bbox
        return f"gZ{left:.6f},{bot:.6f},{right:.6f},{top:.6f}"

    @classmethod
    async def fetch_search(cls, query: QueryParams, intention=None):
        return run_in_threadpool(
            pj_source.search_places,
            query,
            intention.description._place_in_query,
        )

    def filter_search_result(self, results, lang=None, normalized_query=None):
        place = next(iter(result_filter.filter_places(normalized_query, results)), None)
        if place:
            return place.load_place(lang=lang)
        return None

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

    async def get_places_bbox(self, params) -> List[PjApiPOI]:
        return await run_in_threadpool(
            self.fetch_places_bbox,
            params.category,
            params.bbox,
            params.place_name,
            params.place_code,
            size=params.size,
            query=params.q,
        )

    def fetch_places_bbox(
        self, categories: List[CategoryEnum], bbox, place_name, place_code, size=10, query=""
    ) -> List[PjApiPOI]:
        if place_name is not None:
            where = f"{place_name} {place_code}'"
        else:
            where = self.format_where(bbox)

        query_params = {
            "what": (query or " ".join(c.pj_what() for c in categories)).strip(),
            "where": where,
            # The API may return less than 'max' items per page, so let's use 'size + 5'
            # as a margin to avoid requesting a second page unnecessarily.
            "max": min(self.PJ_RESULT_MAX_SIZE, size + 5),
        }

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
            if 400 <= e.response.status_code < 500:
                logger.debug(
                    "Got HTTP %s from PagesJaunes API", e.response.status_code, exc_info=True
                )
                raise PlaceNotFound from e
            raise


pj_source = PagesJaunes()
