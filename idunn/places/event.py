from .base import BasePlace
from .place import PlaceMeta


class Event(BasePlace):
    PLACE_TYPE = 'event'

    # For now, only "openagenda" events are fetched
    EVENT_SOURCE_OPENAGENDA = 'openagenda'

    def get_local_name(self):
        return self.get('title', '')

    def get_id(self):
        event_id = self.get('uid')
        if event_id:
            return f'event:{self.EVENT_SOURCE_OPENAGENDA}:{event_id}'
        return None

    def get_coord(self):
        return self.get('geo_loc')

    def get_website(self):
        return self.get('link')

    def get_images_urls(self):
        images = [self.get('image_thumb')] + [self.get('image')]
        return list(filter(None, images))

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
        return PlaceMeta(source=self.EVENT_SOURCE_OPENAGENDA)
