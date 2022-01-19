from functools import cached_property
from urllib.parse import urlencode

from .base import BasePlace
from idunn import settings
from idunn.api.constants import PoiSource

OSM_CONTRIBUTION_HASHTAGS = settings["OSM_CONTRIBUTION_HASHTAGS"]


def get_name(properties, lang):
    """
    Return the Place name from the properties field of the elastic response. Here 'name'
    corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

    If lang is None or if name:lang is not in the properties then name receives the local name
    value.

    >>> get_name({}, 'fr') is None
    True

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, None)
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'cz')
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'fr')
    'spontinifr'
    """
    name = properties.get(f"name:{lang}")
    if name is None:
        name = properties.get("name")
    return name


class POI(BasePlace):
    PLACE_TYPE = "poi"

    def __init__(self, d):
        super().__init__(d)
        if not isinstance(self.get("properties"), dict):
            self["properties"] = {p.get("key"): p.get("value") for p in self.get("properties", [])}
        self.properties = self["properties"]

    def get_local_name(self):
        return self.properties.get("name", "")

    def get_name(self, lang):
        return get_name(self.properties, lang)

    def get_class_name(self):
        return self.properties.get("poi_class")

    def get_subclass_name(self):
        return self.properties.get("poi_subclass")

    def get_source(self):
        return PoiSource.OSM

    @cached_property
    def osm_id_tuple(self):
        poi_id = self.get_id()
        try:
            _prefix, osm_kind, osm_id = poi_id.rsplit(":", 2)
            return (osm_kind, osm_id)
        except ValueError:
            return tuple()

    def get_source_url(self):
        try:
            osm_kind, osm_id = self.osm_id_tuple
            return f"https://www.openstreetmap.org/{osm_kind}/{osm_id}"
        except ValueError:
            return None

    def get_contribute_url(self):
        try:
            osm_kind, osm_id = self.osm_id_tuple
            edit_params = {osm_kind: osm_id}
            if OSM_CONTRIBUTION_HASHTAGS:
                edit_params["hashtags"] = OSM_CONTRIBUTION_HASHTAGS
            return f"https://www.openstreetmap.org/edit?{urlencode(edit_params)}"
        except ValueError:
            return None


class BragiPOI(POI):
    def __init__(self, bragi_feature):
        coord = bragi_feature.get("geometry", {}).get("coordinates") or []
        if len(coord) == 2:
            lon, lat = coord
        else:
            lon, lat = None, None
        es_dict = dict(bragi_feature["properties"]["geocoding"], coord={"lon": lon, "lat": lat})
        super().__init__(es_dict)

    def get_raw_street(self):
        raw_address = self.get_raw_address()
        return {"name": raw_address.get("street")}

    def get_postcodes(self):
        postcode = self.get("postcode")
        if postcode:
            return [postcode]
        return None

    def get_country_codes(self):
        return [c.upper() for c in self.get_raw_address().get("country_codes") or []]
