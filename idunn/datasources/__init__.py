import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Datasource(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def get_places_bbox(self, params) -> list:
        """Get places within a given Bbox"""
