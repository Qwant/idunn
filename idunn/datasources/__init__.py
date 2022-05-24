import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Datasource(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def get_places_bbox(self, params) -> list:
        """Get places within a given Bbox"""

    @abstractmethod
    async def fetch_search(cls, query, location, intention=None):
        """
        Create a task that will asynchronously search results for a specific query from the /search
        bragi endpoint or for the search PJ api
        """

    @abstractmethod
    def filter_search_result(cls, results, lang, normalized_query):
        """Filter results from the `fetch_search` query"""
