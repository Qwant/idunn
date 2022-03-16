import re
from functools import cached_property
from urllib.parse import urlencode

from idunn import settings
from idunn.api.constants import PoiSource
from .base import BasePlace
from abc import abstractmethod

OSM_CONTRIBUTION_HASHTAGS = settings["OSM_CONTRIBUTION_HASHTAGS"]
TRIPADVISOR_AVAILABLE_LANGS = [
    "fr",
    "de",
    "cl",
    "ca",
    "co",
    "it",
    "es",
    "se",
    "nl",
    "dk",
    "ie",
    "at",
    "pt",
    "ch",
    "jp",
    "in",
]
TRIPADVISOR_AVAILABLE_LANGS_EXTENSION = [
    "br",
    "mx",
    "ar",
    "pe",
    "ve",
    "tr",
    "my",
    "gr",
    "au",
    "ph",
    "sg",
    "vn",
    "hk",
]
REGEX_FIND_DOMAIN_EXTENSION = re.compile(r"(.*?)(com)(.*)")


def get_name(properties, lang):
    """
    Return the Place name from the properties field of the elastic response. Here 'name'
    corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

    If lang is None or if name:lang is not in the properties then name receives the local name
    value.

    >>> get_name({}, 'fr') is None
    True

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, None)
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'cz')
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'fr')
    'spontinifr'
    """
    name = properties.get(f"name:{lang}")
    if name is None:
        name = properties.get("name")
    return name


class POI(BasePlace):
    PLACE_TYPE = "poi"

    def __init__(self, d):
        super().__init__(d)
        if not isinstance(self.get("properties"), dict):
            self["properties"] = {p.get("key"): p.get("value") for p in self.get("properties", [])}
        self.properties = self["properties"]

    def get_local_name(self):
        return self.properties.get("name", "")

    def get_name(self, lang):
        """
        Return the Place name from the properties field of the elastic response. Here 'name'
        corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

        If lang is None or if name:lang is not in the properties then name receives the local name
        value.

        >>> get_name({}, 'fr') is None
        True

        >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, None)
        'spontini'

        >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'cz')
        'spontini'

        >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'fr')
        'spontinifr'
        """
        name = self.properties.get(f"name:{lang}")
        if name is None:
            name = self.properties.get("name")
        return name

    def get_class_name(self):
        return self.properties.get("poi_class")

    def get_subclass_name(self):
        return self.properties.get("poi_subclass")

    @abstractmethod
    def get_source_url(self):
        pass

    @abstractmethod
    def get_contribute_url(self):
        pass

    @abstractmethod
    def get_source(self):
        pass


class OsmPOI(POI):
    @cached_property
    def osm_id_tuple(self):
        poi_id = self.get_id()
        try:
            _prefix, osm_kind, osm_id = poi_id.rsplit(":", 2)
            return (osm_kind, osm_id)
        except ValueError:
            return tuple()

    def get_source_url(self):
        try:
            osm_kind, osm_id = self.osm_id_tuple
            return f"https://www.openstreetmap.org/{osm_kind}/{osm_id}"
        except ValueError:
            return None

    def get_contribute_url(self):
        try:
            osm_kind, osm_id = self.osm_id_tuple
            edit_params = {osm_kind: osm_id}
            if OSM_CONTRIBUTION_HASHTAGS:
                edit_params["hashtags"] = OSM_CONTRIBUTION_HASHTAGS
            return f"https://www.openstreetmap.org/edit?{urlencode(edit_params)}"
        except ValueError:
            return None

    def get_source(self):
        return PoiSource.OSM


class TripadvisorPOI(POI):
    def __init__(self, d, lang):
        super().__init__(d)
        self.lang = lang

    def get_source_url(self):
        return self.get_tripadvisor_lang_url()

    def get_contribute_url(self):
        return self.get_tripadvisor_lang_url()

    def get_source(self):
        return PoiSource.TRIPADVISOR

    def get_raw_grades(self):
        if self.properties.get("ta:average_rating") is None:
            return None
        return {
            "total_grades_count": self.properties.get("ta:review_count"),
            "global_grade": self.properties.get("ta:average_rating"),
        }

    def get_reviews_url(self):
        return f"{self.get_tripadvisor_lang_url()}#REVIEWS"

    # Tripadvisor subclasses are not matching OSM subclasses : Tripadvisor classes are more generic
    def get_subclass_name(self):
        return self.properties.get("poi_class")

    # Tripadvisor already provide the full address in the label field
    def build_address(self, lang):
        raw_address = self.get_raw_address()
        label = raw_address.get("label")

        return {
            "id": "",
            "name": label,
            "housenumber": "",
            "postcode": "",
            "label": label,
            "admin": self.build_admin(lang),
            "street": "",
            "admins": self.build_admins(lang),
            "country_code": "",
        }

    def get_tripadvisor_lang_url(self):
        tripadvisor_default_url = self.properties.get("ta:url")
        if self.lang in TRIPADVISOR_AVAILABLE_LANGS:
            return re.sub(
                REGEX_FIND_DOMAIN_EXTENSION, rf"\1{self.lang}\3", tripadvisor_default_url, count=1
            )
        if self.lang in TRIPADVISOR_AVAILABLE_LANGS_EXTENSION:
            return re.sub(
                REGEX_FIND_DOMAIN_EXTENSION,
                rf"\1\2.{self.lang}\3",
                tripadvisor_default_url,
                count=1,
            )
        return tripadvisor_default_url


# Bragi POI is only used for OSM right now
class BragiPOI(OsmPOI):
    def __init__(self, source: PoiSource, bragi_feature):
        coord = bragi_feature.get("geometry", {}).get("coordinates") or []
        if len(coord) == 2:
            lon, lat = coord
        else:
            lon, lat = None, None
        es_dict = dict(bragi_feature["properties"]["geocoding"], coord={"lon": lon, "lat": lat})
        self.source = source
        super().__init__(es_dict)

    def get_raw_street(self):
        raw_address = self.get_raw_address()
        return {"name": raw_address.get("street")}

    def get_postcodes(self):
        postcode = self.get("postcode")
        if postcode:
            return [postcode]
        return None

    def get_country_codes(self):
        return [c.upper() for c in self.get_raw_address().get("country_codes") or []]

    def get_source(self):
        return self.source


class PoiFactory:
    def get_poi(self, d, lang) -> POI:
        """Get the matching POI type to fetch POIs"""
        if settings["TRIPADVISOR_ENABLED"] and d["id"].startswith("ta:"):
            return TripadvisorPOI(d, lang)
        return OsmPOI(d)
