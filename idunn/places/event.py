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
        event_id = self.get('uid')
        if event_id:
            return  f'event:openagenda:{event_id}'
        return None

    def get_coord(self):
        return self.get('geo_loc')

    # def get_lang(self):
    #   return self.get('lang')

    def get_website(self):
        return self.get('link')

    def get_images_urls(self):
        return [self.get('image_thumb', ''), self.get('image', '')]

    def get_updated_at(self):
        return self.get('updated_at')

    def get_class_name(self):
        return self.get('poi_class')

    def get_subclass_name(self):
        return self.get('poi_subclass')


    def build_address(self, lang):
        """
        Method to build the address field for an Address,
        a Street, an Admin or a POI.
        """

        return {
            "name": self.get('placename'),
            "label": self.get('address'),
            "city": self.get('city'),
            "admin": self.build_admin(lang),
            "admins": self.build_admins(),
        }

    def get_meta(self):
        return PlaceMeta(source='openagenda')

