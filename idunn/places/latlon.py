from .address import Address
from .base import BasePlace


class Latlon(BasePlace):
    PLACE_TYPE = "latlon"

    def __init__(self, lat, lon, closest_address=None):
        self.lat = round(float(lat), 5)
        self.lon = round(float(lon), 5)
        self.closest_address = closest_address or Address({})
        super().__init__(self.closest_address)

    def build_address(self, lang):
        if self.closest_address:
            return self.closest_address.build_address(lang)
        return None

    def get_id(self):
        return f"latlon:{self.lat:.5f}:{self.lon:.5f}"

    def get_local_name(self):
        return f"{self.lat:.5f} : {self.lon:.5f}"

    def get_coord(self):
        return {"lat": self.lat, "lon": self.lon}
