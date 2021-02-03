import logging
from itertools import islice
from geopy.distance import distance

from idunn import settings
from idunn.utils.auth_session import AuthSession
from idunn.utils.redis import RedisWrapper

logger = logging.getLogger(__name__)


class RecyclingAuthSession(AuthSession):
    def get_authorization_url(self):
        base_url = settings.get("RECYCLING_SERVER_URL")
        return f"{base_url}/_login/local"

    def get_authorization_params(self):
        return {
            "username": settings["RECYCLING_SERVER_USERNAME"],
            "password": settings["RECYCLING_SERVER_PASSWORD"],
        }

    @staticmethod
    def parse_authorisation_response(resp):
        token = resp["result"]["jwt"]
        expires_at = resp["result"]["expiresAt"] / 1000
        return token, expires_at

    def query_new_token(self):
        return self.inner.get(
            self.get_authorization_url(),
            json=self.get_authorization_params(),
            timeout=self.refresh_timeout,
        )


class RecyclingDataSource:
    def __init__(self):
        self.request_timeout = float(settings["RECYCLING_REQUEST_TIMEOUT"])
        self.data_index = settings["RECYCLING_DATA_INDEX"]
        self.data_collection = settings["RECYCLING_DATA_COLLECTION"]
        self.timestamp_field = settings["RECYCLING_DATA_TIMESTAMP_FIELD"]
        self.use_cache = settings["RECYCLING_DATA_STORE_IN_CACHE"]
        self.cache_expire = int(settings["RECYCLING_DATA_EXPIRE"])
        self.measures_max_age_in_hours = int(settings["RECYCLING_MEASURES_MAX_AGE_IN_HOURS"])
        self.session = RecyclingAuthSession(refresh_timeout=self.request_timeout)

    @property
    def base_url(self):
        return settings.get("RECYCLING_SERVER_URL")

    @property
    def enabled(self):
        return bool(self.base_url)

    def get_latest_measures(self, lat, lon, max_distance, size=50):
        """
        If cache is used, latest measures will be fetched and cached with a larger radius.

        Arbitrary values are used in that case:
            max_distance: 10 km
            lat and lon: rounded to 1 decimal

        This ensures that all measure points are covered by at least 1 cache key, with a tolerance
        of 2km. At the equator, distance((0,0),(0.05,0.05)) is 7.9 km.
        """
        if not self.use_cache:
            return self._fetch_latest_measures(lat, lon, max_distance=max_distance, size=size)

        assert max_distance <= 2000, "Cached recycling data cannot be retrieved for radius > 2km"
        rounded_lat, rounded_lon = f"{lat:.1f}", f"{lon:.1f}"
        key = f"recycling_latest_measures_{rounded_lat}_{rounded_lon}"
        results = RedisWrapper.cache_it(key, self._fetch_latest_measures, expire=self.cache_expire)(
            rounded_lat, rounded_lon, max_distance=10_000, size=10_000
        )

        if not results:
            return []

        def get_distance_of_result(r):
            measure_geoloc = r["_source"]["metadata"]["location"]["geolocation"]
            return distance((lat, lon), (measure_geoloc["lat"], measure_geoloc["lon"])).meters

        return list(islice((r for r in results if get_distance_of_result(r) < max_distance), size))

    def _fetch_latest_measures(self, lat, lon, max_distance, size):
        query = {
            "bool": {
                "filter": [
                    {
                        "range": {
                            self.timestamp_field: {"gte": f"now-{self.measures_max_age_in_hours}h"}
                        }
                    },
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
                "sort": {self.timestamp_field: "desc"},
            },
            params={"size": size},
            timeout=self.request_timeout,
        )

        response.raise_for_status()
        return response.json().get("result", {}).get("hits", [])


recycling_client = RecyclingDataSource()
