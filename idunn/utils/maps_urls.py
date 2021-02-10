from urllib.parse import urlencode
from idunn import settings
from idunn.geocoder.models.geocodejson import IntentionFilter


MAPS_BASE_URL = settings["MAPS_BASE_URL"]


def get_default_url(no_ui=False):
    url = MAPS_BASE_URL
    if no_ui:
        url += "?no_ui=1"
    return url


def get_place_url(place_id, no_ui=False):
    url = f"{MAPS_BASE_URL}place/{place_id}"
    if no_ui:
        url += "?no_ui=1"
    return url


def get_places_url(filter: IntentionFilter, no_ui=False):
    query_dict = {}
    if filter.q:
        query_dict["q"] = filter.q
    if filter.category:
        query_dict["type"] = filter.category
    if filter.source:
        query_dict["source"] = filter.source
    if filter.bbox:
        query_dict["bbox"] = ",".join(map(lambda x: f"{x:.6f}", filter.bbox))
    if no_ui:
        query_dict["no_ui"] = 1
    return f"{MAPS_BASE_URL}places/?{urlencode(query_dict)}"


def get_directions_url(place_id):
    query_dict = {"destination": place_id}
    return f"{MAPS_BASE_URL}routes/?{urlencode(query_dict)}"
