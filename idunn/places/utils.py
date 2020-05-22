from fastapi import HTTPException
from idunn.api.pages_jaunes import pj_source
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.api.utils import fetch_es_place, PlaceNotFound
from idunn.utils import prometheus


from .admin import Admin
from .street import Street
from .address import Address
from .poi import POI
from .latlon import Latlon
from .exceptions import InvalidPlaceId, RedirectToPlaceId


def place_from_id(id, type=None):
    """
    :param id: place id
    :param type: Optional type to restrict query in Elasticsearch
    :return: Place
    """
    try:
        namespace, suffix = id.split(":", 1)
    except ValueError:
        raise InvalidPlaceId(id)

    # Handle place from "pages jaunes"
    if namespace == pj_source.PLACE_ID_NAMESPACE:
        return pj_source.get_place(id)

    # Simple latlon place id
    if namespace == Latlon.PLACE_ID_NAMESPACE:
        return Latlon.from_id(id)

    # Otherwise handle places from the ES db
    es = get_elasticsearch()

    try:
        es_place = fetch_es_place(id, es, type)
    except PlaceNotFound as e:
        if namespace == "addr":
            # A Latlon place can be used as a substitute for a "addr:<lon>;<lat>" id
            # that is not present in the database anymore
            try:
                lon, lat = suffix.split(":", 1)[0].split(";")
                latlon_id = Latlon(lat=lat, lon=lon).get_id()
            except ValueError:
                pass
            else:
                raise RedirectToPlaceId(latlon_id)
        raise HTTPException(status_code=404, detail=e.message)

    places = {
        "admin": Admin,
        "street": Street,
        "addr": Address,
        "poi": POI,
    }
    loader = places.get(es_place.get("_type"))

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        raise Exception(
            "Place with id '{}' has a wrong type: '{}'".format(id, es_place[0].get("_type"))
        )
    return loader(es_place["_source"])
