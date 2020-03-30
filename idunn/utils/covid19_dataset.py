import logging
import csv
import json
from datetime import datetime, timedelta
import requests
from idunn import settings
from idunn.utils.redis import RedisWrapper, CacheNotAvailable
from pydantic import BaseModel
from redis.lock import LockError

logger = logging.getLogger(__name__)
COVID19_OSM_DATASET_STATE_KEY = "covid19_osm_dataset_state"
COVID19_POI_STATUS_KEY_PREFIX = "covid19_poi_"

last_check_datetime = datetime(2020, 1, 1)


class CovidOsmDatasetState(BaseModel):
    updated_at: datetime


class OsmPoiCovidStatus(BaseModel):
    osm_id: str
    name: str
    cat: str
    brand: str
    wikidata: str
    url_hours: str
    infos: str
    status: str
    opening_hours: str
    lon: float
    lat: float
    updated_at: datetime


def should_update_covid19_osm_dataset():
    """
    Update covid data
    """
    try:
        state = RedisWrapper.get_json(COVID19_OSM_DATASET_STATE_KEY)
    except CacheNotAvailable:
        return False
    return state is None


def update_covid19_osm_dataset():
    if not should_update_covid19_osm_dataset():
        return

    updated_at = datetime.utcnow().isoformat()
    new_state = CovidOsmDatasetState(updated_at=updated_at)
    RedisWrapper._set_value(
        COVID19_OSM_DATASET_STATE_KEY,
        new_state.json(),
        expire=settings["COVID19_OSM_DATASET_EXPIRE"],
    )

    response = requests.get(
        settings["COVID19_OSM_DATASET_URL"],
        headers={"User-Agent": settings["WIKI_USER_AGENT"]},
        stream=True,
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    dict_reader = csv.DictReader(response.iter_lines(decode_unicode=True))
    pipe = RedisWrapper._connection.pipeline(transaction=False)
    count = 0
    for row in dict_reader:
        poi_id = f"osm:{row['osm_id'].replace('/', ':')}"
        row["updated_at"] = updated_at
        pipe.set(
            f"{COVID19_POI_STATUS_KEY_PREFIX}{poi_id}",
            json.dumps(row),
            ex=settings["COVID19_POI_EXPIRE"],
        )
        count += 1
        if count % 1000 == 0:
            pipe.execute()
    pipe.execute()
    logger.info("Success. %s POIs have been written from Covid19 dataset to Redis", count)


def get_poi_covid_status(place_id):
    if not RedisWrapper.init_cache():
        return None

    try:
        value = RedisWrapper.get_json(f"{COVID19_POI_STATUS_KEY_PREFIX}{place_id}")
        if not value:
            return None
        return OsmPoiCovidStatus(**value)
    except CacheNotAvailable:
        return None
    except Exception:
        logger.exception("Failed to parse poi covid status for %s", place_id)
        return None


def covid19_osm_task():
    global last_check_datetime
    if datetime.utcnow() < last_check_datetime + timedelta(minutes=2):
        # Useless to check for data freshness too often
        return

    if not RedisWrapper.init_cache():
        # Redis is not configured
        return

    try:
        with RedisWrapper._connection.lock(
            "covid19_osm_task_lock_key", blocking_timeout=1, timeout=1800
        ):
            last_check_datetime = datetime.utcnow()
            update_covid19_osm_dataset()
    except LockError:
        logger.info("Failed to acquire lock to run covid19_osm_task")
