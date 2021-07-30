from idunn.api.constants import WIKIDATA_TO_BBOX_OVERRIDE
from .base import BasePlace


class Admin(BasePlace):
    PLACE_TYPE = "admin"

    def __init__(self, d):
        super().__init__(d)
        if not isinstance(self.get("codes"), dict):
            self["codes"] = {p.get("name"): p.get("value") for p in self.get("codes", [])}
        self.codes = self["codes"]

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

    @property
    def wikidata_id(self):  # pylint: disable=invalid-overridden-method
        return self.codes.get("wikidata") or None
