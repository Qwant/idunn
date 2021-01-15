from .base import BasePlace


class Street(BasePlace):
    PLACE_TYPE = "street"

    def get_raw_street(self):
        return self

    def get_postcodes(self):
        return self.get("zip_codes")

    def get_bbox(self):
        raise NotImplementedError
