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
