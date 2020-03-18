import requests
from .base import BasePlace
from .place import PlaceMeta
from idunn.api.utils import get_name


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

    def get_meta(self):
        return PlaceMeta(source="osm")


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
