import re
from functools import lru_cache
from statistics import mean, StatisticsError
from typing import Union

from .base import BasePlace
from .models import pj_info, pj_find
from .place import PlaceMeta
from ..api.constants import PoiSource

WHEELCHAIN_ACCESSIBLE = re.compile(
    "|".join(
        [
            "accès handicapés?",
            "accès aux personnes à mobilité réduite",
            "accès pour personne à mobilité réduite",
        ]
    )
)

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


class PjApiPOI(BasePlace):
    PLACE_TYPE = "poi"

    def __init__(self, d: Union[pj_find.Listing, pj_info.Response]):
        super().__init__(d)
        self.data = d

    def get_id(self):
        merchant_id = self.data.merchant_id
        return f"pj:{merchant_id}" if merchant_id else None

    def get_coord(self):
        if isinstance(self.data, pj_info.Response):
            # TODO: it seems the information is not here?
            return {"lat": 48, "lon": 2}

        return next(
            (
                {"lat": ins.latitude, "lon": ins.longitude}
                for ins in self.data.inscriptions or []
                if ins.latitude and ins.longitude
            ),
            None,
        )

    def get_local_name(self):
        return self.data.merchant_name or ""

    def get_contact_infos(self):
        if isinstance(self.data, pj_info.Response):
            return (
                contact
                for ins in self.data.inscriptions or []
                for contact in ins.contact_infos or []
            )
        else:
            return (
                contact
                for ins in self.data.inscriptions or []
                for contact in ins.contact_info or []
            )

    def get_phone(self):
        return next(
            (
                contact.contact_value
                for contact in self.get_contact_infos()
                if contact.contact_type.value in ["MOBILE", "TELEPHONE"]
            ),
            None,
        )

    def get_website(self):
        return next((site.website_url for site in self.data.website_urls or []), None)

    def get_class_name(self):
        class_name, _ = get_class_subclass(
            frozenset(cat.category_name for cat in self.data.categories or [])
        )
        return class_name

    def get_subclass_name(self):
        _, subclass_name = get_class_subclass(
            frozenset(cat.category_name for cat in self.data.categories or [])
        )
        return subclass_name

    def get_raw_opening_hours(self):
        if isinstance(self.data, pj_info.Response) and self.data.schedules:
            return self.data.schedules.opening_hours
        elif isinstance(self.data, pj_find.Listing):
            return self.data.opening_hours
        return None

    def get_raw_wheelchair(self):
        return (
            any(
                WHEELCHAIN_ACCESSIBLE.match(label)
                for desc in self.data.business_descriptions or []
                for label in (desc.values or [])
            )
            or None
        )

    def get_inscription_with_address(self):
        """Search for an inscriptions that contains address informations"""
        return next((ins for ins in self.data.inscriptions or [] if ins.address_street), None)

    def build_address(self, lang):
        inscription = self.get_inscription_with_address()

        if not inscription:
            return None

        city = inscription.address_city
        postcode = inscription.address_zipcode
        street_and_number = inscription.address_street

        return {
            "id": None,
            "name": street_and_number,
            "housenumber": None,
            "postcode": postcode,
            "label": f"{street_and_number}, {postcode} {city}".strip().strip(","),
            "admin": None,
            "admins": self.build_admins(lang),
            "street": {
                "id": None,
                "name": None,
                "label": None,
                "postcodes": [postcode] if postcode else [],
            },
            "country_code": self.get_country_code(),
        }

    def build_admins(self, lang=None):
        inscription = self.get_inscription_with_address()

        if not inscription:
            return None

        city = inscription.address_city
        postcode = inscription.address_zipcode

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

    def get_country_codes(self):
        return ["FR"]

    def get_images_urls(self):
        images = []

        if self.data.thumbnail_url:
            images.append(self.data.thumbnail_url)

        if isinstance(self.data, pj_info.Response):
            images += [photo.url for photo in self.data.photos or []]

        return images or None

    def get_meta(self):
        return PlaceMeta(source=PoiSource.PAGESJAUNES)

    def get_raw_grades(self):
        grade_count = sum(
            ins.reviews.total_reviews for ins in self.data.inscriptions or [] if ins.reviews
        )

        try:
            grade_avg = mean(
                ins.reviews.overall_review_rating
                for ins in self.data.inscriptions or []
                if ins.reviews and ins.reviews.overall_review_rating > 0
            )
        except StatisticsError:
            # Empty reviews
            return None

        return {
            "total_grades_count": grade_count,
            "global_grade": grade_avg,
        }

    def get_reviews_url(self):
        return next(
            (
                ins.urls.reviews_url
                for ins in self.data.inscriptions or []
                if ins.urls and ins.urls.reviews_url
            ),
            None,
        )
