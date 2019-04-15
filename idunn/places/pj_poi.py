from .base import BasePlace
from .place import PlaceMeta

class PjPOI(BasePlace):
    PLACE_TYPE = 'poi'

    def get_id(self):
        business_id = self.get('BusinessId')
        if business_id:
            return f'pj:{business_id}'
        return None

    def get_coord(self):
        return self.get('Geo')

    def get_local_name(self):
        return self.get('BusinessName', '')

    def get_phone(self):
        phone_numbers = self.get('ContactInfos', {}).get('PhoneNumbers', [])
        if phone_numbers:
            return phone_numbers[0].get('phoneNumber')
        return None

    def get_website(self):
        return self.get('WebsiteURL')

    def get_class_name(self):
        raw_categories = set(self.get('Category', []))
        if 'restaurants' in raw_categories:
            return 'restaurant'
        if 'hôtels' in raw_categories:
            return 'lodging'
        if 'musées' in raw_categories:
            return 'museum'
        if 'salles de cinéma' in raw_categories:
            return 'cinema'
        if 'salles de concerts, de spectacles' in raw_categories:
            return 'theatre'
        return None

    def get_subclass_name(self):
        return self.get_class_name()

    def get_raw_opening_hours(self):
        opening_hours_dict = self.get('OpeningHours', {})
        raw = ""
        for k in ['Mo','Tu','We','Th','Fr','Sa','Su']:
            value = opening_hours_dict.get(k)
            if value:
                raw += f'{k} {value}; '
        return raw.rstrip('; ')

    def get_raw_wheelchair(self):
        return self.get('WheelchairAccessible')

    def build_address(self, lang):
        raw_address = self.get('Address', {})
        city = raw_address.get('City', '')
        number = raw_address.get('Number', '')
        postal_code = raw_address.get('PostalCode', '')
        street = raw_address.get('Street', '')

        return {
            "id": None,
            "name": f'{number} {street}'.strip(),
            "housenumber": number,
            "postcode": postal_code,
            "label": f'{number} {street}, {postal_code} {city}'.strip(),
            "admin": None,
            "admins": [],
            "street": {
                "id": None,
                "name": street,
                "label": f'{street} ({city})',
                "postcodes": [postal_code] if postal_code else []
            }
        }

    def get_images_urls(self):
        photos = self.get('photos', {}).get('photos', [])
        return [p.get('url', '') for p in photos]

    def get_meta(self):
        return PlaceMeta(source='pagesjaunes')
