from statistics import mean, StatisticsError

from .base import BasePlace
from .models.pj_business import Response, ContactType
from .place import PlaceMeta
from ..api.constants import PoiSource


class PjPOI(BasePlace):
    PLACE_TYPE = "poi"

    def __init__(self, d):
        super().__init__(d)
        self.data = Response(**d)

    def get_id(self):
        business_id = self.data.merchant_id
        return f"pj:{business_id}" if business_id else None

    def get_coord(self):
        # TODO
        pass

    def get_local_name(self):
        return self.data.merchant_name or ""

    def get_phone(self):
        print(self.data)
        return next(
            (
                contact.contact_value
                for inscription in self.data.inscriptions or []
                for contact in inscription.contact_infos or []
                if contact.contact_type in [ContactType.MOBILE, ContactType.TELEPHONE]
            ),
            None,
        )

    def get_website(self):
        return next((site.website_url for site in self.data.website_urls or []), None)

    def get_class_name(self):
        # TODO : check that this still matches
        pass

    def get_subclass_name(self):
        # TODO : check that this still matches
        pass

    def get_raw_opening_hours(self):
        # TODO
        pass

    def get_raw_wheelchair(self):
        # TODO: need the API to look into the format
        pass

    def get_inscription_with_address(self):
        """Search for an inscriptions that contains address informations"""
        # TODO: is the filter relevant?
        # TODO: should we also check HeadOfficeAddress?
        return next((ins for ins in self.data.inscriptions or [] if ins.address_street), None)

    def build_address(self, lang):
        inscription = self.get_inscription_with_address()

        if not inscription:
            return None

        city = inscription.address_city
        postcode = inscription.address_postal_box
        street_and_number = inscription.address_street

        try:
            # TODO: this method isn't quire robust:
            #       "46 Ter rue ...", "58-60 rue ..."
            words = street_and_number.split()
            number = int(words[0])
            street = " ".join(words[1:])
        except (IndexError, ValueError):
            number = None
            street = street_and_number

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

    def get_raw_address(self):
        return {}

    def get_country_codes(self):
        return ["FR"]

    def get_images_urls(self):
        # TODO: do we have a mechanism to use "thumbnail"?
        return [photo.url for photo in self.data.photos or []]

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
                if ins.reviews
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
