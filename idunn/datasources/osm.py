import asyncio
import logging
from copy import deepcopy

from starlette.concurrency import run_in_threadpool

from idunn.api.constants import PoiSource
from idunn.datasources import Datasource
from idunn.datasources.mimirsbrunn import fetch_es_pois, MimirPoiFilter
from idunn.geocoder.bragi_client import bragi_client
from idunn.geocoder.models.params import SearchQueryParams
from idunn.places.poi import BragiPOI, OsmPOI
from idunn.utils.place import place_from_id

logger = logging.getLogger(__name__)

SUBCLASS_HOTEL_OSM = [
    "subclass_hotel",
    "subclass_lodging",
]


class Osm(Datasource):
    is_wiki_search: bool = False

    def __init__(self, is_wiki_search: bool):
        super().__init__()
        self.is_wiki_search = is_wiki_search

    @classmethod
    def fetch_search(
        cls, query: SearchQueryParams, intentions=None, is_france_query=False, is_wiki=False
    ):
        query_osm = deepcopy(query)
        if cls.is_wiki_search:
            query_osm.wikidata = True
            query_osm.except_poi_types = SUBCLASS_HOTEL_OSM
        return asyncio.create_task(bragi_client.search(query), name="ia_fetch_bragi")

    @classmethod
    def filter_search_result(cls, results, lang, normalized_query=None):
        try:
            feature_properties = results["features"][0]["properties"]["geocoding"]
            place_id = feature_properties["id"]
            place = place_from_id(place_id, lang, follow_redirect=True)
            return place.load_place(lang=lang)
        except Exception:
            return None

    async def get_places_bbox(self, params) -> list:
        """Get places within a given Bbox"""
        if params.q:
            # Default source (OSM) with query
            bragi_response = await bragi_client.pois_query_in_bbox(
                query=params.q, bbox=params.bbox, lang=params.lang, limit=params.size
            )
            return [BragiPOI(PoiSource.OSM, f) for f in bragi_response.get("features", [])]

        if params.raw_filter:
            filters = [MimirPoiFilter.from_url_raw_filter(f) for f in params.raw_filter]
        else:
            filters = [f for c in params.category for f in c.raw_filters()]
        bbox_places = await run_in_threadpool(
            fetch_es_pois,
            "poi",
            filters=filters,
            bbox=params.bbox,
            max_size=params.size,
        )
        return [OsmPOI(p["_source"]) for p in bbox_places]
