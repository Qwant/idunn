from functools import lru_cache
from .base import BasePlace
from .place import PlaceMeta
from ..api.constants import PoiSource

DOCTORS = (
    "Chiropracteur",
    "Centre de radiologie",
    "Cardiologue",
    "Gynécologue",
    "ORL",
    "Radiologue",
    "Ostéopathe",
    "Chirurgien",
    "Ophtalmologue",
    "Médecin généraliste",
    "Infirmier",
    "kinésithérapeute",
    "Psychologue",
    "Ergothérapeute",
)


@lru_cache(maxsize=200)
def get_class_subclass(raw_categories):
    categories = [
        {"raw": "restaurants", "class": "restaurant"},
        {"raw": "hôtels", "class": "lodging"},
        {"raw": "salles de cinéma", "class": "cinema"},
        {"raw": "salles de concerts, de spectacles", "class": "theatre"},
        {"raw": "Pharmacie", "class": "pharmacy"},
        {"raw": "supermarchés, hypermarchés", "class": "grocery"},
        {"raw": "banques", "class": "bank"},
        {"raw": "cafés, bars", "class": "bar"},
        {"raw": "Chirurgien-dentiste", "class": "dentist"},
        {"raw": "musées", "class": "museum"},
        {"raw": "Hôpital", "class": "hospital"},
        {"raw": "garages automobiles", "class": "car", "subclass": "car_repair"},
        {"raw": "envoi, distribution de courrier, de colis", "class": "post_office"},
        {"raw": "mairies", "class": "town_hall"},
        {"raw": "services de gendarmerie, de police", "class": "police"},
        {"raw": "sapeurs-pompiers, centres de secours", "class": "fire_station"},
        {"raw": "infrastructures de sports et loisirs", "class": "sports_centre"},
        {"raw": "piscines (établissements)", "class": "sports_centre"},
        {"raw": "clubs de sport", "class": "sports_centre"},
        {"raw": "vétérinaires", "class": "veterinary"},
        {
            "class": "school",
            "func": lambda raw_categories: any(
                k in c for c in raw_categories for k in ("écoles ", "collèges ", "lycées ")
            ),
        },
        {
            "class": "college",
            "func": lambda raw_categories: any(
                "enseignement supérieur" in c for c in raw_categories
            ),
        },
        {
            "class": "doctors",
            "func": lambda raw_categories: any(k in c for c in raw_categories for k in DOCTORS),
        },
    ]
    for category in categories:
        if "raw" in category:
            if category["raw"] in raw_categories:
                class_name = category["class"]
                subclass_name = category.get("subclass") or class_name
                return (class_name, subclass_name)
        elif "func" in category:
            if category["func"](raw_categories):
                class_name = category["class"]
                subclass_name = category.get("subclass") or class_name
                return (class_name, subclass_name)
    return (None, None)


class PjPOI(BasePlace):
    PLACE_TYPE = "poi"

    def get_id(self):
        business_id = self.get("BusinessId")
        if business_id:
            return f"pj:{business_id}"
        return None

    def get_coord(self):
        return self.get("Geo")

    def get_local_name(self):
        return self.get("BusinessName", "")

    def get_phone(self):
        phone_numbers = self.get("ContactInfos", {}).get("PhoneNumbers", [])
        if phone_numbers:
            return phone_numbers[0].get("phoneNumber")
        return None

    def get_website(self):
        return self.get("WebsiteURL")

    def get_class_name(self):
        raw_categories = frozenset(self.get("Category", []))
        class_name, _ = get_class_subclass(raw_categories)
        return class_name

    def get_subclass_name(self):
        raw_categories = frozenset(self.get("Category", []))
        _, subclass_name = get_class_subclass(raw_categories)
        return subclass_name

    def get_raw_opening_hours(self):
        opening_hours_dict = self.get("OpeningHours", {})
        raw = ""

        def format_day_range(first_day, last_day, times):
            if not times:
                return ""
            if first_day == last_day:
                return f"{first_day} {times}; "
            return f"{first_day}-{last_day} {times}; "

        first_day, last_day, times = ("", "", "")
        for k in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            value = opening_hours_dict.get(k)
            if not value or value != times:
                raw += format_day_range(first_day, last_day, times)
                first_day = ""
                last_day = ""
                times = ""
            if value and value != times:
                first_day = k
                last_day = k
                times = value
            if value and value == times:
                last_day = k
        raw += format_day_range(first_day, last_day, times)
        result = raw.rstrip("; ")

        if result == "Mo-Su 24/7":
            return "24/7"

        return result

    def get_raw_wheelchair(self):
        return self.get("WheelchairAccessible")

    def build_address(self, lang):
        city = self.get_city()
        postcode = self.get_postcode()
        number = self.raw_address().get("Number", "")
        street = self.raw_address().get("Street", "")

        return {
            "id": None,
            "name": f"{number} {street}".strip(),
            "housenumber": number,
            "postcode": postcode,
            "label": f"{number} {street}, {postcode} {city}".strip().strip(","),
            "admin": None,
            "admins": self.build_admins(lang),
            "street": {
                "id": None,
                "name": street,
                "label": f"{street} ({city})",
                "postcodes": [postcode] if postcode else [],
            },
            "country_code": self.get_country_code(),
        }

    def build_admins(self, lang=None):
        city = self.get_city()
        postcode = self.get_postcode()

        if postcode:
            label = f"{city} ({postcode})"
        else:
            label = city

        return [
            {
                "name": city,
                "label": label,
                "class_name": "city",
                "postcodes": [postcode] if postcode else [],
            }
        ]

    def raw_address(self):
        return self.get("Address", {})

    def get_city(self):
        return self.raw_address().get("City", "")

    def get_postcode(self):
        return self.raw_address().get("PostalCode", "")

    def get_country_codes(self):
        return ["FR"]

    def get_images_urls(self):
        photos = self.get("photos", {}).get("photos", [])
        return [p.get("url", "") for p in photos]

    def get_meta(self):
        return PlaceMeta(source=PoiSource.PAGESJAUNES)

    def get_raw_grades(self):
        return self.get("grades")

    def get_reviews_url(self):
        return self.get("Links", {}).get("viewReviews", "")
