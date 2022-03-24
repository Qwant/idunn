import httpx
from typing import Optional

from idunn import settings
from idunn.datasources.hove.models import HoveResponse
from idunn.directions.models import IdunnTransportMode
from idunn.places.base import BasePlace


DIRECT_PATH_MAX_DURATION = 86400  # 24h
MIN_NB_JOURNEYS = 2
MAX_NB_JOURNEYS = 5


class HoveClient:
    def __init__(self):
        self.api_url = settings["HOVE_API_BASE_URL"]
        self.session = httpx.AsyncClient(verify=settings["VERIFY_HTTPS"])
        self.session.headers["User-Agent"] = settings["USER_AGENT"]

    async def directions(
        self,
        start: BasePlace,
        end: BasePlace,
        mode: IdunnTransportMode,
        _lang: str,
        _extra: Optional[dict] = None,
    ) -> HoveResponse:
        start = start.get_coord()
        end = end.get_coord()

        params = {
            "from": f"{start['lon']};{start['lat']}",
            "to": f"{end['lon']};{end['lat']}",
            "max_walking_direct_path_duration": DIRECT_PATH_MAX_DURATION,
            "max_bike_direct_path_duration": DIRECT_PATH_MAX_DURATION,
            "max_car_no_park_direct_path_duration": DIRECT_PATH_MAX_DURATION,
            "min_nb_journeys": MIN_NB_JOURNEYS,
            "max_nb_journeys": MAX_NB_JOURNEYS,
        }

        if mode == IdunnTransportMode.PUBLICTRANSPORT:
            params.update({"direct_path": "none"})
        else:
            params.update(
                {
                    "direct_path_mode[]": mode.to_hove(),
                    "direct_path": "only",
                }
            )

        response = await self.session.get(
            self.api_url,
            params=params,
            headers={"Authorization": settings["HOVE_API_TOKEN"]},
        )

        response.raise_for_status()
        return HoveResponse(**response.json())

    async def directions_hove(self, *args, **kwargs):
        return (await self.directions(*args, **kwargs)).as_api_response()


client = HoveClient()
