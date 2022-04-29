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
    def fetch_search(cls, query, intentions=None, is_france_query=False, is_wiki=False):
        """async call"""

    @abstractmethod
    def filter(cls, results, lang, normalized_query):
        """filter response"""
