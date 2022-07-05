from abc import ABC, abstractmethod, abstractstaticmethod
from typing import Optional

from idunn.datasources.directions.mapbox.models import DirectionsResponse, IdunnTransportMode
from idunn.geocoder.models.params import QueryParams
from idunn.places.base import BasePlace


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
        extra: Optional[QueryParams] = None,
    ) -> DirectionsResponse:
        ...
