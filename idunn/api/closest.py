import logging

from fastapi import HTTPException
from pydantic import confloat

from idunn import settings
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.utils import prometheus
from idunn.places import Street, Address
from idunn.api.utils import fetch_closest, Verbosity

logger = logging.getLogger(__name__)


MAX_DISTANCE_IN_METERS = 500


def get_closest_place(lat: float, lon: float, es=None):
    if es is None:
        es = get_elasticsearch()
    es_addr = fetch_closest(lat, lon, es=es, max_distance=MAX_DISTANCE_IN_METERS)

    places = {
        "addr": Address,
        "street": Street,
    }
    loader = places.get(es_addr.get("_type"))

    if loader is None:
        logger.warning("Found a place with the wrong type")
        prometheus.exception("FoundPlaceWithWrongType")
        raise HTTPException(
            status_code=404,
            detail="Closest address to '{}:{}' has a wrong type: '{}'".format(
                lat, lon, es_addr.get("_type")
            ),
        )

    return loader(es_addr["_source"])


def closest_address(
    lat: confloat(ge=-90, le=90),
    lon: confloat(ge=-180, le=180),
    lang=None,
    verbosity: Verbosity = Verbosity.default(),
) -> Address:
    """Find the closest address to a point."""

    es = get_elasticsearch()

    if not lang:
        lang = settings["DEFAULT_LANGUAGE"]
    lang = lang.lower()

    place = get_closest_place(lat, lon, es)
    return place.load_place(lang, verbosity)
