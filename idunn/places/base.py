import logging

from idunn.api.utils import WikidataConnector, get_geom, build_blocks
from idunn.blocks import WikiUndefinedException, GET_WIKI_INFO, WikipediaCache
from .place import Place, PlaceMeta


logger = logging.getLogger(__name__)

class BasePlace(dict):
    PLACE_TYPE = ''

    def __init__(self, d):
        if not self.PLACE_TYPE:
            raise Exception(
                'Missing PLACE_TYPE in class %s',
                self.__class__.__name__
            )
        super().__init__(d)
        self._wiki_resp = {}
        self.properties = {}

    def get_wiki_info(self, wikidata_id, wiki_index):
        return WikidataConnector.get_wiki_info(wikidata_id, wiki_index)

    def get_wiki_index(self, lang):
        return WikidataConnector.get_wiki_index(lang)

    def get_wiki_resp(self, lang):
        if lang not in self._wiki_resp:
            self._wiki_resp[lang] = None
            wikidata_id = self.wikidata_id
            if wikidata_id is not None:
                wiki_index = self.get_wiki_index(lang)
                if wiki_index is not None:
                    key = GET_WIKI_INFO + "_" + wikidata_id + "_" + lang + "_" + wiki_index
                    try:
                        self._wiki_resp[lang] = WikipediaCache.cache_it(key, WikidataConnector.get_wiki_info)(wikidata_id, wiki_index)
                    except WikiUndefinedException:
                        logger.info("WIKI_ES variable has not been set: cannot fetch wikidata images")
                        return None
        return self._wiki_resp.get(lang)

    @property
    def wikidata_id(self):
        return self.properties.get('wikidata')

    def get_name(self, lang):
        return self.get_local_name()

    def get_local_name(self):
        return self.get('name', '')

    def get_class_name(self):
        return self.PLACE_TYPE

    def get_subclass_name(self):
        return self.PLACE_TYPE

    def get_raw_address(self):
        return self.get('address') or {}

    def get_raw_street(self):
        raw_address = self.get_raw_address()
        if raw_address.get('type') == 'street':
            return raw_address
        return raw_address.get("street") or {}

    def get_raw_admins(self):
        return self.get("administrative_regions") or []

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
                postcodes = ';'.join(postcodes)

        id = raw_address.get("id")
        name = raw_address.get("name")
        housenumber = raw_address.get("house_number")
        label = raw_address.get("label")

        return {
            "id": id,
            "name": name,
            "housenumber": housenumber,
            "postcode": postcodes,
            "label": label,
            "admin": self.build_admin(lang),
            "street": self.build_street(),
            "admins": self.build_admins(),
        }

    def build_admin(self, lang=None):
        return None

    def build_admins(self):
        raw_admins = self.get_raw_admins()
        admins = []
        if not raw_admins is None:
            for raw_admin in raw_admins:
                admin = {
                    "id": raw_admin.get("id"),
                    "label": raw_admin.get("label"),
                    "name": raw_admin.get("name"),
                    "class_name": raw_admin.get("zone_type"),
                    "postcodes": raw_admin.get("zip_codes")
                }
                admins.append(admin)
        return admins

    def build_street(self):
        raw_street = self.get_raw_street()
        return {
            "id": raw_street.get("id"),
            "name": raw_street.get("name"),
            "label": raw_street.get("label"),
            "postcodes": raw_street.get("zip_codes")
        }

    def get_id(self):
        return self.get('id', '')

    def find_property_value(self, fallback_keys):
        for k in fallback_keys:
            val = self.properties.get(k)
            if val:
                return val
        return None

    def get_phone(self):
        return self.find_property_value(['phone', 'contact:phone'])

    def get_website(self):
        return self.find_property_value(['contact:website', 'website', 'facebook'])

    def get_coord(self):
        return self.get('coord')

    def get_raw_opening_hours(self):
        return self.properties.get('opening_hours')

    def get_raw_wheelchair(self):
        return self.properties.get("wheelchair")

    def get_meta(self):
        return PlaceMeta()

    def load_place(self, lang, verbosity):
        return Place(
            type=self.PLACE_TYPE,
            id=self.get_id(),
            name=self.get_name(lang),
            local_name=self.get_local_name(),
            class_name=self.get_class_name(),
            subclass_name=self.get_subclass_name(),
            geometry=get_geom(self),
            address=self.build_address(lang),
            blocks=build_blocks(self, lang, verbosity),
            meta=self.get_meta()
        )

    def get_images_urls(self):
        return []

    def get_raw_grades(self):
        return {}
