import logging
import re
from geopy import Point
from pytz import timezone, UTC

from idunn.api.utils import Verbosity, build_blocks
from idunn.datasources.wiki_es import wiki_es
from idunn.utils import maps_urls, tz
from .place import Place, PlaceMeta


logger = logging.getLogger(__name__)


ZONE_TYPE_ORDER_KEY = {
    "suburb": 1,
    "city_district": 2,
    "city": 3,
    "state_district": 4,
    "state": 5,
    "country_region": 6,
    "country": 7,
}


class BasePlace(dict):
    PLACE_TYPE = ""

    def __init__(self, d):
        if not self.PLACE_TYPE:
            raise Exception(f"Missing PLACE_TYPE in class {self.__class__.__name__}")
        super().__init__(d)
        self._wiki_resp = {}
        self.properties = {}

    @property
    def wikidata_id(self):
        return self.properties.get("wikidata")

    def get_wiki_resp(self, lang):
        if lang not in self._wiki_resp:
            self._wiki_resp[lang] = None

            if (
                self.wikidata_id is not None
                and wiki_es.enabled()
                and wiki_es.is_lang_available(lang)
            ):
                self._wiki_resp[lang] = wiki_es.get_info(self.wikidata_id, lang)

        return self._wiki_resp.get(lang)

    def get_name(self, _lang):
        return self.get_local_name()

    def get_local_name(self):
        return self.get("name", "")

    def get_class_name(self):
        return self.PLACE_TYPE

    def get_subclass_name(self):
        return self.PLACE_TYPE

    def get_raw_address(self):
        return self.get("address") or {}

    def get_raw_street(self):
        raw_address = self.get_raw_address()
        if raw_address.get("type") == "street":
            return raw_address
        return raw_address.get("street") or {}

    def get_raw_admins(self):
        return self.get("administrative_regions") or []

    def get_country_codes(self):
        """
        The list of codes is ordered from the least specific to the most specific
        For example for a placed located in La Réunion: ["FR","RE","RE"]
        for the country, the state ("région") and the state_district ("département")
        :return: List of ISO 3166-1 alpha-2 country codes
        """
        ordered_admins = sorted(
            self.get_raw_admins(),
            key=lambda a: ZONE_TYPE_ORDER_KEY.get(a.get("zone_type"), 0),
            reverse=True,
        )
        return [c.upper() for admin in ordered_admins for c in admin.get("country_codes", [])]

    def get_country_code(self):
        return next(iter(self.get_country_codes()), None)

    def get_postcodes(self):
        return self.get_raw_address().get("zip_codes")

    def build_address(self, lang):
        """
        Method to build the address field for an Address,
        a Street, an Admin or a POI.
        """
        raw_address = self.get_raw_address()
        postcodes = self.get_postcodes()
        if postcodes is not None:
            if isinstance(postcodes, list):
                if len(postcodes) == 1:
                    postcodes = postcodes[0]
                else:
                    postcodes = None

        addr_id = raw_address.get("id")
        name = raw_address.get("name")
        label = raw_address.get("label")
        street = self.build_street()

        # ES raw data uses "house_number" whereas Bragi returns "housenumber"
        housenumber = raw_address.get("house_number") or raw_address.get("housenumber")

        return {
            "id": addr_id,
            "name": name or street.get("name"),
            "housenumber": housenumber,
            "postcode": postcodes,
            "label": label or street.get("label"),
            "admin": self.build_admin(lang),
            "street": street,
            "admins": self.build_admins(lang),
            "country_code": self.get_country_code(),
        }

    def build_admin(self, _lang=None):
        return None

    def build_admins(self, lang=None) -> list:
        raw_admins = self.get_raw_admins()
        admins = []
        if not raw_admins is None:
            for raw_admin in raw_admins:
                admin = {
                    "id": raw_admin.get("id"),
                    "label": raw_admin.get("labels", {}).get(lang) or raw_admin.get("label"),
                    "name": raw_admin.get("names", {}).get(lang) or raw_admin.get("name"),
                    "class_name": raw_admin.get("zone_type"),
                    "postcodes": raw_admin.get("zip_codes"),
                }
                admins.append(admin)
        return admins

    def build_street(self):
        raw_street = self.get_raw_street()
        return {
            "id": raw_street.get("id"),
            "name": raw_street.get("name"),
            "label": raw_street.get("label"),
            "postcodes": raw_street.get("zip_codes"),
        }

    def get_id(self):
        return self.get("id", "")

    def find_property_value(self, fallback_keys):
        for k in fallback_keys:
            val = self.properties.get(k)
            if val:
                return val
        return None

    def get_phone(self):
        phone = self.find_property_value(["phone", "contact:phone", "contact:mobile"])
        if phone is None:
            return None
        return phone.split(";")[0]

    def get_website(self):
        return self.find_property_value(["contact:website", "website"])

    def get_website_label(self):
        return None

    @staticmethod
    def build_social_if_not_url(template, field):
        if field is None or re.match("^https?://", field):
            return field

        return template.format(field.lstrip("@"))

    def get_facebook(self):
        return self.build_social_if_not_url(
            "https://www.facebook.com/{}",
            self.find_property_value(["facebook", "contact:facebook"]),
        )

    def get_twitter(self):
        return self.build_social_if_not_url(
            "https://twitter.com/{}",
            self.find_property_value(["twitter", "contact:twitter"]),
        )

    def get_instagram(self):
        return self.build_social_if_not_url(
            "https://www.instagram.com/{}",
            self.find_property_value(["instagram", "contact:instagram"]),
        )

    def get_youtube(self):
        return self.build_social_if_not_url(
            "https://www.youtube.com/{}",
            self.find_property_value(["contact:youtube"]),
        )

    def get_coord(self):
        return self.get("coord")

    def get_point(self):
        coord = self.get_coord()
        return Point(latitude=coord["lat"], longitude=coord["lon"])

    def get_raw_opening_hours(self):
        return self.properties.get("opening_hours")

    def get_raw_wheelchair(self):
        return self.properties.get("wheelchair")

    def get_source(self):
        return None

    def get_source_url(self):
        return None

    def get_contribute_url(self):
        return None

    def get_meta(self):
        place_id = self.get_id()
        return PlaceMeta(
            source=self.get_source(),
            source_url=self.get_source_url(),
            contribute_url=self.get_contribute_url(),
            maps_place_url=maps_urls.get_place_url(place_id),
            maps_directions_url=maps_urls.get_directions_url(place_id),
        )

    def load_place(self, lang, verbosity: Verbosity = Verbosity.default()) -> Place:
        return Place(
            type=self.PLACE_TYPE,
            id=self.get_id(),
            name=self.get_name(lang),
            local_name=self.get_local_name(),
            class_name=self.get_class_name(),
            subclass_name=self.get_subclass_name(),
            geometry=self.get_geometry(),
            address=self.build_address(lang),
            blocks=build_blocks(self, lang, verbosity),
            meta=self.get_meta(),
        )

    def get_images_urls(self):
        return []

    def get_raw_grades(self):
        return {}

    def get_reviews_url(self):
        return ""

    def get_booking_url(self):
        return None

    def get_appointment_url(self):
        return None

    def get_quotation_request_url(self):
        return None

    def get_description(self, lang):
        return self.properties.get(f"description:{lang}")

    def get_description_url(self, _lang):
        return None

    def has_click_and_collect(self):
        return False

    def has_delivery(self):
        return self.properties.get("delivery") == "yes"

    def has_takeaway(self):
        return self.properties.get("takeaway") in ("yes", "only")

    def get_bbox(self):
        return None

    def get_tz(self):
        """
        >>> from idunn.places import POI

        >>> poi1 = POI({"coord": {"lon": 2.3, "lat":48.9}})
        >>> poi1.get_tz().zone
        'Europe/Paris'

        >>> poi2 = POI({'coord':{"lon":-12.8218, "lat": 37.5118}})
        >>> poi2.get_tz().zone
        'UTC'
        """
        coords = self.get_coord()
        tz_name = tz.tzNameAt(latitude=coords["lat"], longitude=coords["lon"], forceTZ=True)
        if tz_name is None:
            return UTC
        return timezone(tz_name)

    def get_geometry(self):
        """Returns GeoJSON-like geometry. Requires "lon" and "lat" coordinates.
        >>> from idunn.places import POI
        >>> assert POI({}).get_geometry() is None

        >>> assert POI({'coord':{"lon": None, "lat": 48.85}}).get_geometry() is None

        >>> assert POI({'coord':{"lon": 2.29, "lat": None}}).get_geometry() is None

        >>> POI({'coord':{"lon": 2.29, "lat": 48.85}}).get_geometry()
        {'type': 'Point', 'coordinates': [2.29, 48.85], 'center': [2.29, 48.85]}
        """
        geom = None
        coord = self.get_coord()
        if coord is not None:
            lon = coord.get("lon")
            lat = coord.get("lat")
            if lon is not None and lat is not None:
                geom = {"type": "Point", "coordinates": [lon, lat], "center": [lon, lat]}
                bbox = self.get_bbox()  # pylint: disable=assignment-from-none
                if bbox is not None:
                    geom["bbox"] = bbox
        return geom
