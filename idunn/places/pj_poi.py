from statistics import mean, StatisticsError
from typing import Union

from .base import BasePlace
from .models import pj_business, pj_find
from .place import PlaceMeta
from ..api.constants import PoiSource


class PjPOI(BasePlace):
    PLACE_TYPE = "poi"

    def __init__(self, d: Union[pj_find.Listing, pj_business.Response]):
        super().__init__(d)
        self.data = d

    def get_id(self):
        listing_id = self.data.listing_id
        return f"pj:{listing_id}" if listing_id else None

    def get_coord(self):
        if isinstance(self.data, pj_business.Response):
            # TODO: it seems the information is not here?
            return {"lat": 0, "lon": 0}

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
        if isinstance(self.data, pj_business.Response):
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
                if contact.contact_type
                in [  # TODO: unify
                    pj_business.ContactType.MOBILE,
                    pj_business.ContactType.TELEPHONE,
                    pj_find.ContactType.MOBILE,
                    pj_find.ContactType.TELEPHONE,
                ]
            ),
            None,
        )

    def get_website(self):
        return next((site.website_url for site in self.data.website_urls or []), None)

    def get_class_name(self):
        # TODO : check that this still matches
        return "cinema"

    def get_subclass_name(self):
        # TODO : check that this still matches
        return "cinema"

    def get_raw_opening_hours(self):
        # TODO
        pass

    def get_raw_wheelchair(self):
        # TODO: need the API to look into the format
        pass

    def get_inscription_with_address(self):
        """Search for an inscriptions that contains address informations"""
        # TODO: is the filter relevant?
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
            "housenumber": None,  # TODO?
            "postcode": postcode,
            "label": f"{street_and_number}, {postcode} {city}".strip().strip(","),
            "admin": None,
            "admins": self.build_admins(lang),
            "street": {  # TODO?
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

    def get_raw_address(self):
        return {}

    def get_country_codes(self):
        return ["FR"]

    def get_images_urls(self):
        # TODO: it could be interesting to distinguish the thumbnail from other images
        thumbnail = self.data.thumbnail_url
        images = [thumbnail] if thumbnail else []

        if isinstance(self.data, pj_business.Response):
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
