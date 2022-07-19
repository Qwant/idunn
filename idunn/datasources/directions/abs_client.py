from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from idunn.geocoder.models.params import QueryParams
from idunn.places.base import BasePlace
from .mapbox.models import DirectionsResponse, IdunnTransportMode


class AbsDirectionsClient(ABC):
    @staticmethod
    @abstractmethod
    def client_name() -> str:
        ...

    @abstractmethod
    async def get_directions(
        self,
        from_place: BasePlace,
        to_place: BasePlace,
        mode: IdunnTransportMode,
        lang: str,
        arrive_by: Optional[datetime],
        depart_at: Optional[datetime],
        extra: Optional[QueryParams] = None,
    ) -> DirectionsResponse:
        ...
