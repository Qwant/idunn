import re
from functools import lru_cache
from statistics import mean, StatisticsError
from typing import List, Optional, Union

from .base import BasePlace
from .models import pj_info, pj_find
from .models.pj_info import TransactionalLinkType, UrlType
from ..api.constants import PoiSource
from ..api.urlsolver import resolve_url


CLICK_AND_COLLECT = re.compile(r"retrait .*")
DELIVERY = re.compile(r"commande en ligne|livraison.*")
TAKEAWAY = re.compile(r".* à emporter")
WHEELCHAIR_ACCESSIBLE = re.compile("accès (handicapés?|(aux|pour) personnes? à mobilité réduite)")

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
    "Psychologue",
    "Ergothérapeute",
)


@lru_cache(maxsize=200)
def get_class_subclass(raw_categories):
    categories = [
        {"raw": "hôtels", "class": "lodging"},
        {"raw": "restaurants", "class": "restaurant"},
        {"raw": "salles de cinéma", "class": "cinema"},
        {"raw": "salles de concerts, de spectacles", "class": "theatre"},
        {"raw": "Pharmacie", "class": "pharmacy"},
        {"raw": "supermarchés, hypermarchés", "class": "supermarket"},
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
        {"raw": "Masseur kinésithérapeute", "class": "health_physiotherapist"},
        {"raw": "restauration rapide", "class": "fast_food"},
        {"raw": "boulangeries-pâtisseries (artisans)", "class": "bakery"},
        {"raw": "coiffeurs", "class": "hairdresser"},
        {
            "class": "clothes",
            "func": lambda raw_categories: any(
                k in c for c in raw_categories for k in ("vêtements", "lingerie")
            ),
        },
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

    def build_admins(self, lang=None) -> list:
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

    def get_source(self):
        return PoiSource.PAGESJAUNES

    def get_source_url(self):
        business_id = self.get("BusinessId")
        if not business_id:
            return None
        return f"https://www.pagesjaunes.fr/pros/{business_id}"

    def get_contribute_url(self):
        source_url = self.get_source_url()

        if not source_url:
            return None

        return f"{source_url}#zone-informations-pratiques"

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
        return next(
            (
                {"lat": ins.latitude, "lon": ins.longitude}
                for ins in self.data.inscriptions
                if ins.latitude and ins.longitude
            ),
            None,
        )

    def get_local_name(self):
        return self.data.merchant_name or ""

    def get_contact_infos(self):
        if isinstance(self.data, pj_info.Response):
            return (contact for ins in self.data.inscriptions for contact in ins.contact_infos)
        return (contact for ins in self.data.inscriptions for contact in ins.contact_info)

    def get_phone(self):
        return next(
            (
                contact.contact_value
                for contact in self.get_contact_infos()
                if contact.contact_type.value in ["MOBILE", "TELEPHONE"]
            ),
            None,
        )

    def get_website_url_for_type(self, site_types: Union[UrlType, List[UrlType]]) -> Optional[str]:
        if isinstance(site_types, UrlType):
            site_types = [site_types]

        return next(
            (
                resolve_url(website.website_url)
                for website in self.data.website_urls or []
                if website.url_type in site_types
            ),
            None,
        )

    WEBSITE_TYPES = [
        UrlType.SITE_EXTERNE,
        UrlType.WEBSITE,
        UrlType.MINISITE,
        UrlType.SITE_PRIVILEGE,
    ]

    def get_website(self):
        return self.get_website_url_for_type(self.WEBSITE_TYPES)

    def get_website_label(self):
        if isinstance(self.data, pj_find.Listing):
            # FIXME: Ideally the Listing would include a "suggested_label" too
            return self.get_local_name()

        prefix = "Voir le site "
        suggested_label = next(
            (
                website.suggested_label
                for website in self.data.website_urls or []
                if website.url_type in self.WEBSITE_TYPES
            ),
            None,
        )

        if not suggested_label:
            return None

        if suggested_label.startswith(prefix):
            return suggested_label[len(prefix) :]

        return suggested_label

    def get_facebook(self):
        return self.get_website_url_for_type(UrlType.FACEBOOK)

    def get_twitter(self):
        return self.get_website_url_for_type(UrlType.TWITTER)

    def get_instagram(self):
        return self.get_website_url_for_type(UrlType.INSTAGRAM)

    def get_youtube(self):
        return self.get_website_url_for_type(UrlType.YOUTUBE)

    def get_class_name(self):
        class_name, _ = get_class_subclass(
            frozenset(cat.category_name for cat in self.data.categories)
        )
        return class_name

    def get_subclass_name(self):
        _, subclass_name = get_class_subclass(
            frozenset(cat.category_name for cat in self.data.categories)
        )
        return subclass_name

    def get_raw_opening_hours(self):
        if isinstance(self.data, pj_info.Response) and self.data.schedules:
            return self.data.schedules.opening_hours
        if isinstance(self.data, pj_find.Listing):
            return self.data.opening_hours
        return None

    def get_raw_wheelchair(self):
        return (
            any(
                WHEELCHAIR_ACCESSIBLE.match(label)
                for desc in self.data.business_descriptions
                for label in desc.values
            )
            or None
        )

    def get_inscription_with_address(self):
        """Search for an inscriptions that contains address informations"""
        return next((ins for ins in self.data.inscriptions if ins.address_street), None)

    def build_address(self, lang):
        inscription = self.get_inscription_with_address()

        if not inscription:
            city, postcode, street_and_number = [""] * 3
        else:
            city = inscription.address_city or ""
            postcode = inscription.address_zipcode or ""
            street_and_number = inscription.address_street or ""

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

    def build_admins(self, lang=None) -> list:
        """
        >>> poi = PjApiPOI(pj_info.Response(**{
        ...    "inscriptions": [
        ...        {
        ...         "address_city": None,
        ...         "address_district": "03",
        ...         "address_street": "5 r Thorigny",
        ...         "address_zipcode": "75003",
        ...         "latitude": 48.859702,
        ...         "longitude": 2.362634,
        ...     }
        ... ]}))
        >>> assert poi.build_admins() == [], f"Got {poi.build_admins()}"
        """
        inscription = self.get_inscription_with_address()

        if not inscription or not inscription.address_city:
            return []

        city = inscription.address_city
        postcode = inscription.address_zipcode or ""

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
            images += [photo.url for photo in self.data.photos]

        return images

    def get_source(self):
        return PoiSource.PAGESJAUNES

    def get_source_url(self):
        return f"https://www.pagesjaunes.fr/pros/{self.data.merchant_id}"

    def get_contribute_url(self):
        source_url = self.get_source_url()

        if not source_url:
            return None

        return f"{source_url}#zone-informations-pratiques"

    def get_raw_grades(self):
        grade_count = sum(
            ins.reviews.total_reviews for ins in self.data.inscriptions if ins.reviews
        )

        try:
            grade_avg = mean(
                ins.reviews.overall_review_rating
                for ins in self.data.inscriptions
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
        return self.get_source_url() + "#ancreBlocAvis"

    def get_transactional_url(self, types_filter: List[TransactionalLinkType]) -> Optional[str]:
        return next(
            (
                resolve_url(link.url)
                for link in self.data.transactionals_links or []
                if link.type in types_filter
            ),
            None,
        )

    def get_booking_url(self):
        return self.get_transactional_url(
            [
                TransactionalLinkType.RESERVER,
                TransactionalLinkType.RESERVER_INTERNE,
                # TransactionalLinkType.RESERVER_LA_FOURCHETTE, # this link seems broken
                TransactionalLinkType.RESERVER_LA_FOURCHETTE_SIMPLE,
                TransactionalLinkType.RESERVER_LA_FOURCHETTE_PROMO,
            ]
        )

    def get_appointment_url(self):
        return self.get_transactional_url(
            [
                TransactionalLinkType.PRENDRE_RDV_CLIC_RDV,
                TransactionalLinkType.PRENDRE_RDV_EXTERNE,
                TransactionalLinkType.PRENDRE_RDV_INTERNE,
            ]
        )

    def get_order_url(self):
        return self.get_transactional_url(
            [
                TransactionalLinkType.COMMANDER,
                TransactionalLinkType.COMMANDER_CHRONO,
            ]
        )

    def get_quotation_request_url(self):
        return self.get_transactional_url([TransactionalLinkType.QUOTATION_REQUEST])

    def get_description(self, lang):
        if lang != "fr" or isinstance(self.data, pj_find.Listing):
            return None

        return self.data.description

    def get_description_url(self, lang):
        if lang != "fr":
            return None

        return self.get_source_url()

    def has_click_and_collect(self):
        return any(
            CLICK_AND_COLLECT.match(label.lower())
            for desc in self.data.business_descriptions
            for label in desc.values
        )

    def has_delivery(self):
        return any(
            DELIVERY.match(label.lower())
            for desc in self.data.business_descriptions
            for label in desc.values
        )

    def has_takeaway(self):
        return any(
            TAKEAWAY.match(label.lower())
            for desc in self.data.business_descriptions
            for label in desc.values
        )

    HOTEL_STARS_REGEX = re.compile(r"hôtel (?P<rating>\d) étoiles?")

    def get_lodging_stars(self) -> Optional[Union[bool, float]]:
        if isinstance(self.data, pj_find.Listing):
            return None

        for acc in self.data.accommodation_infos or []:
            if match := self.HOTEL_STARS_REGEX.match(acc.category):
                return float(match.group("rating"))

        return None

    def get_restaurant_stars(self) -> Optional[Union[bool, float]]:
        if isinstance(self.data, pj_find.Listing) or not self.data.restaurant_info:
            return None

        return "restaurant étoilé" in (self.data.restaurant_info.atmospheres or [])
