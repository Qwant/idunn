from .address import Address
from .base import BasePlace
from .exceptions import InvalidPlaceId


class Latlon(BasePlace):
    PLACE_TYPE = "latlon"
    PLACE_ID_NAMESPACE = "latlon"

    def __init__(self, lat, lon, closest_address=None):
        self.lat = round(float(lat), 5)
        self.lon = round(float(lon), 5)
        self.closest_address = closest_address or Address({})
        super().__init__(self.closest_address)

    @classmethod
    def from_id(cls, latlon_id):
        try:
            _namespace, lat, lon = latlon_id.split(":")
        except ValueError as exc:
            raise InvalidPlaceId(latlon_id) from exc
        return cls(lat, lon)

    def build_address(self, lang):
        if self.closest_address:
            return self.closest_address.build_address(lang)
        return None

    def get_id(self):
        return f"{self.PLACE_ID_NAMESPACE}:{self.lat:.5f}:{self.lon:.5f}"

    def get_local_name(self):
        return f"{self.lat:.5f} : {self.lon:.5f}"

    def get_coord(self):
        return {"lat": self.lat, "lon": self.lon}

    def get_bbox(self):
        raise NotImplementedError
