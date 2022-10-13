from urllib.parse import urlencode
from idunn import settings
from idunn.geocoder.models.geocodejson import Intention

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


def get_places_url(intention: Intention, no_ui=False):
    query_dict = {}
    if intention.filter.q:
        query_dict["q"] = intention.filter.q
    if intention.filter.category:
        query_dict["type"] = intention.filter.category
    if intention.filter.source:
        query_dict["source"] = intention.filter.source
    if intention.filter.bbox:
        query_dict["bbox"] = ",".join(map(lambda x: f"{x:.6f}", intention.filter.bbox))
    if intention.description.place["properties"]["geocoding"]["citycode"]:
        query_dict["city_code"] = intention.description.place["properties"]["geocoding"]["citycode"]
    if intention.description.place["properties"]["geocoding"]["name"]:
        query_dict["city_name"] = intention.description.place["properties"]["geocoding"]["name"]
    if no_ui:
        query_dict["no_ui"] = 1
    return f"{MAPS_BASE_URL}places/?{urlencode(query_dict)}"


def get_directions_url(place_id):
    query_dict = {"destination": place_id}
    return f"{MAPS_BASE_URL}routes/?{urlencode(query_dict)}"
