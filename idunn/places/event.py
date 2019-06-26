from .base import BasePlace
from .place import PlaceMeta
from idunn.api.utils import get_name


class Event(BasePlace):
    PLACE_TYPE = 'event'

    def __init__(self, d):
        super().__init__(d)

    def get_local_name(self):
        return self.get('title', '')

    def get_id(self):
        return self.get('uid')

    def get_coord(self):
        return self.get('geo_loc')

    # def get_lang(self):
    #   return self.get('lang')

    def get_website(self):
        return self.get('link')

    def get_images_urls(self):
        images = [self.get('image_thumb')] + [self.get('image')]
        return list(filter(None, images))

    def get_updated_at(self):
        return self.get('updated_at')

    def get_class_name(self):
        return None

    def get_subclass_name(self):
        return self.get('poi_subclass')


    def build_address(self, lang):
        """
        Method to build the address field for an Address,
        a Street, an Admin or a POI.
        """

        return {
            "name": self.get('placename'),
            "region": self.get('region'),
            "department": self.get('department'),
            "label": self.get('address'),
            "city": self.get('city'),
            "admin": self.build_admin(lang),
            "admins": self.build_admins(),
        }

    def get_meta(self):
        return PlaceMeta(source='openagenda')

