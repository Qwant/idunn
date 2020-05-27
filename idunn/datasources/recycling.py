from datetime import datetime
from time import time
import requests
import logging
from idunn import settings

logger = logging.getLogger(__name__)


class RecyclingDataSource:
    def __init__(self):
        self.session = requests.Session()
        self.request_timeout = float(settings["RECYCLING_REQUEST_TIMEOUT"])
        self.data_index = settings["RECYCLING_DATA_INDEX"]
        self.data_collection = settings["RECYCLING_DATA_COLLECTION"]

        self._token_expires_at = 0

    @property
    def base_url(self):
        return settings.get("RECYCLING_SERVER_URL")

    @property
    def enabled(self):
        return bool(self.base_url)

    def refresh_token(self):
        current_epoch_millis = int(time() * 1000)
        expiration_tolerance = 10000  # refresh token expiring in less than 10s
        if current_epoch_millis < self._token_expires_at - expiration_tolerance:
            return

        self.session.headers.pop("Authorization", None)
        resp = self.session.get(
            f"{self.base_url}/_login/local",
            json={
                "username": settings["RECYCLING_SERVER_USERNAME"],
                "password": settings["RECYCLING_SERVER_PASSWORD"],
            },
            timeout=self.request_timeout,
        )
        resp.raise_for_status()
        token = resp.json()["result"]["jwt"]
        self._token_expires_at = resp.json()["result"]["expiresAt"]
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get_latest_measures(self, lat, lon, max_distance=100, size=50):
        self.refresh_token()
        query = {
            "bool": {
                "filter": [
                    {"range": {"hour": {"gte": "now-7d"}}},
                    {
                        "nested": {
                            "path": "metadata.location",
                            "query": {
                                "bool": {
                                    "filter": [
                                        {
                                            "geo_distance": {
                                                "distance": f"{max_distance}m",
                                                "metadata.location.geolocation": {
                                                    "lon": lon,
                                                    "lat": lat,
                                                },
                                            }
                                        }
                                    ]
                                }
                            },
                        }
                    },
                ]
            }
        }

        response = self.session.post(
            f"{self.base_url}/{self.data_index}/{self.data_collection}/_search",
            json={
                "query": query,
                # keep the latest document for each measuring point
                "collapse": {"field": "measuringPointId"},
                "sort": {"hour": "desc"},
            },
            params={"size": size},
            timeout=self.request_timeout,
        )

        response.raise_for_status()
        return response.json().get("result", {}).get("hits", [])


recycling_client = RecyclingDataSource()
