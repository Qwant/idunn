from functools import cached_property
from idunn.api.constants import WIKIDATA_TO_BBOX_OVERRIDE
from .base import BasePlace


class Admin(BasePlace):
    PLACE_TYPE = "admin"

    def build_admin(self, lang=None):
        labels = self.get("labels", {})
        return {"label": labels.get(lang) or self.get("label")}

    def get_postcodes(self):
        return self.get("zip_codes")

    def get_name(self, lang):
        return self.get("names", {}).get(lang) or self.get_local_name()

    def get_bbox(self):
        if self.wikidata_id in WIKIDATA_TO_BBOX_OVERRIDE:
            return WIKIDATA_TO_BBOX_OVERRIDE[self.wikidata_id]
        return self.get("bbox")

    def get_class_name(self):
        return self.get("zone_type")

    def get_subclass_name(self):
        return self.get("zone_type")

    @cached_property
    def wikidata_id(self):  # pylint: disable=invalid-overridden-method
        codes = self.get("codes")
        if codes is None:
            return None
        for entry in codes:
            if entry["name"] == "wikidata":
                return entry["value"]
        return None
