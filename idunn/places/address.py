from .base import BasePlace
from idunn.api.utils import build_blocks, get_geom

class Address(BasePlace):
    PLACE_TYPE = 'address'

    def get_raw_address(self):
        return self

    def get_raw_admins(self):
        return self.get_raw_street().get("administrative_regions") or []
