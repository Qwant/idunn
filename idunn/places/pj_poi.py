from .base import BasePlace
from .place import PlaceMeta
from ..api.constants import SOURCE_PAGESJAUNES

HEALTH = (
    'Chiropracteur',
    'Centre de radiologie',
    'Cardiologue',
    'Gynécologue',
    'ORL',
    'Radiologue',
    'Centre médico-social',
    'Ostéopathe',
    'santé publique',
    'médecine sociale',
    'médecine du travail',
    'Chirurgien',
    'dentiste',
    'Ophtalmologue',
    'Médecin généraliste',
    'Infirmier',
    'soins à domicile',
    'kinésithérapeute',
    'Psychologue',
    'Ergothérapeute',
    'préfectures',
    'sous-préfectures',
    'Hôpital',
    'Pharmacie',
    'vétérinaires',
)

SERVICE = (
    'plombiers',
    'garages automobiles',
    'mécanique générale',
    'envoi, distribution de courrier, de colis',
    'serrurerie, métallerie',
    'mairies',
    ' gendarmerie',
    ' police',
    'sapeurs-pompiers',
    'centres de secours',
    'entreprises de menuiserie',
)


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
        categories = [
            {'raw': 'restaurants', 'name': 'restaurant'},
            {'raw': 'hôtels', 'name': 'lodging'},
            {'raw': 'salles de cinéma', 'name': 'cinema'},
            {'raw': 'salles de concerts, de spectacles', 'name': 'theatre'},
            {'raw': 'Pharmacie', 'name': 'pharmacy'},
            {'raw': 'supermarchés, hypermarchés', 'name': 'grocery'},
            {'raw': 'banques', 'name': 'bank'},
            {'raw': 'cafés, bars', 'name': 'bar'},
            {'name': 'school',
             'func': lambda raw_categories: any(k in c
                                                for c in raw_categories
                                                for k in ('écoles ', 'collèges ', 'lycées '))},
            {'name': 'college',
             'func': lambda raw_categories: any('enseignement supérieur' in c for c in raw_categories)},
            {'raw': 'musées', 'name': 'museum'},
            {'name': 'health',
             'func': lambda raw_categories: any(k in c for c in raw_categories for k in HEALTH)},
            {'name': 'service',
             'func': lambda raw_categories: any(k in c for c in raw_categories for k in SERVICE)},
            {'raw': 'agences immobilière', 'name': 'building'},
        ]
        for category in categories:
            if 'raw' in category:
                if category['raw'] in raw_categories:
                    return category['name']
            elif 'func' in category:
                if category['func'](raw_categories):
                    return category['name']
        return None

    def get_subclass_name(self):
        return self.get_class_name()

    def get_raw_opening_hours(self):
        opening_hours_dict = self.get('OpeningHours', {})
        raw = ""

        def format_day_range(first_day, last_day, times):
            if not times:
                return ''
            if first_day == last_day:
                return f'{first_day} {times}; '
            return f'{first_day}-{last_day} {times}; '

        first_day, last_day, times = ('', '', '')
        for k in ['Mo','Tu','We','Th','Fr','Sa','Su']:
            value = opening_hours_dict.get(k)
            if not value or value != times:
                raw += format_day_range(first_day, last_day, times)
                first_day = ''
                last_day = ''
                times = ''
            if value and value != times:
                first_day = k
                last_day = k
                times = value
            if value and value == times:
                last_day = k
        raw += format_day_range(first_day, last_day, times)
        result = raw.rstrip('; ')

        if result == 'Mo-Su 24/7':
            return '24/7'

        return result

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
            "label": f'{number} {street}, {postal_code} {city}'.strip().strip(','),
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
        return PlaceMeta(source=SOURCE_PAGESJAUNES)

    def get_raw_grades(self):
        return self.get('grades')

    def get_reviews_url(self):
        return self.get('Links', {}).get('viewReviews', '')
