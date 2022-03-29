import logging

from fastapi.concurrency import run_in_threadpool

from idunn.api.constants import PoiSource
from idunn.datasources import Datasource
from idunn.datasources.mimirsbrunn import fetch_es_pois, MimirPoiFilter
from idunn.geocoder.bragi_client import bragi_client
from idunn.places.poi import BragiPOI, OsmPOI

logger = logging.getLogger(__name__)


class Osm(Datasource):
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
