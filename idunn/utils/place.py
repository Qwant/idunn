from idunn.datasources.mimirsbrunn import fetch_es_place, get_es_place_type
from idunn.utils.es_wrapper import get_mimir_elasticsearch
from idunn.utils import prometheus

from ..datasources.pages_jaunes import pj_source
from ..places import Latlon, Admin, Address, Street
from ..places.exceptions import InvalidPlaceId, PlaceNotFound, RedirectToPlaceId
from ..places.poi import POI, PoiFactory


def place_from_id(id: str, lang: str, type=None, follow_redirect=False):
    """
    :param id: place id
    :param type: Optional type to restrict query in Elasticsearch
    :param follow_redirect: if false, RedirectToPlaceId may be raised
    :return: Place
    """
    try:
        namespace, suffix = id.split(":", 1)
    except ValueError as exc:
        raise InvalidPlaceId(id) from exc

    # Handle place from "pages jaunes"
    if namespace == pj_source.PLACE_ID_NAMESPACE:
        return pj_source.get_place(id)

    # Handle place from tripadvisor
    if namespace == "ta":
        type = "poi_tripadvisor"

    # Simple latlon place id
    if namespace == Latlon.PLACE_ID_NAMESPACE:
        return Latlon.from_id(id)

    # Otherwise handle places from the ES db
    es = get_mimir_elasticsearch()
    try:
        es_place = fetch_es_place(id, es, type)
    except PlaceNotFound as exc:
        if namespace == "addr":
            # A Latlon place can be used as a substitute for a "addr:<lon>;<lat>" id
            # that is not present in the database anymore
            try:
                lon, lat = suffix.split(":", 1)[0].split(";")
                latlon_id = Latlon(lat=lat, lon=lon).get_id()
            except ValueError:
                pass
            else:
                if not follow_redirect:
                    raise RedirectToPlaceId(latlon_id) from exc
                return place_from_id(latlon_id, lang, follow_redirect=False)
        raise

    places = {
        "admin": Admin,
        "street": Street,
        "addr": Address,
        "poi": POI,
        "poi_tripadvisor": POI,
    }

    place_type = get_es_place_type(es_place)
    loader = places.get(place_type)

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        raise Exception(f"Place with id '{id}' has a wrong type: '{place_type}'")

    if loader is POI:
        return PoiFactory().get_poi(es_place["_source"], lang=lang)
    return loader(es_place["_source"])
