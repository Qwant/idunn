import logging
from abc import ABC, abstractmethod, abstractproperty
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Callable, Optional


from idunn import settings
from idunn.datasources.directions.abs_client import AbsDirectionsClient
from idunn.geocoder.models import QueryParams
from idunn.places.base import BasePlace
from .hove.client import HoveClient
from .mapbox.client import MapboxClient
from .mapbox.models import DirectionsResponse, IdunnTransportMode

logger = logging.getLogger(__name__)


class MapboxAPIExtraParams(BaseModel):
    steps: str = "true"
    alternatives: str = "true"
    overview: str = "full"
    geometries: str = "geojson"
    exclude: Optional[str]


class DirectionsClient(AbsDirectionsClient):
    def __init__(self):
        self.mapbox = MapboxClient()
        self.hove = HoveClient()

    @staticmethod
    def client_name() -> str:
        return "generic"

    def get_method_for_mode(self, mode: IdunnTransportMode) -> AbsDirectionsClient:
        methods = {"mapbox": self.mapbox, "hove": self.hove}

        match mode:
            case IdunnTransportMode.CAR:
                return methods[settings["DIRECTIONS_PROVIDER_DRIVE"]]
            case IdunnTransportMode.BIKE:
                return methods[settings["DIRECTIONS_PROVIDER_CYCLE"]]
            case IdunnTransportMode.WALKING:
                return methods[settings["DIRECTIONS_PROVIDER_WALK"]]
            case IdunnTransportMode.PUBLICTRANSPORT:
                return methods[settings["DIRECTIONS_PROVIDER_PUBLICTRANSPORT"]]

    @staticmethod
    def place_to_url_coords(place):
        coord = place.get_coord()
        lat, lon = coord["lat"], coord["lon"]
        return (f"{lon:.5f}", f"{lat:.5f}")

    async def get_directions(
        self,
        from_place: BasePlace,
        to_place: BasePlace,
        mode: IdunnTransportMode,
        lang: str,
        extra: Optional[QueryParams] = None,
    ) -> DirectionsResponse:
        idunn_mode = IdunnTransportMode.parse(mode)

        if idunn_mode is None:
            raise HTTPException(status_code=400, detail=f"unknown mode {mode}")

        method = self.get_method_for_mode(idunn_mode)

        logger.info(
            "Calling directions API '%s'",
            method.client_name(),
            extra={
                "method": method.client_name(),
                "mode": idunn_mode,
                "lang": lang,
                "from_place": from_place.get_id(),
                "to_place": to_place.get_id(),
            },
        )

        # pylint: disable = not-callable
        return await method.get_directions(from_place, to_place, idunn_mode, lang, extra)


directions_client = DirectionsClient()
