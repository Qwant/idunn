from apistar import types, validators
from idunn.blocks.base import BlocksValidator
from idunn.api.utils import LONG, BLOCKS_BY_VERBOSITY

class Place(types.Type):
    PLACE_TYPE = ''

    type = validators.String()
    id = validators.String(allow_null=True)
    name = validators.String(allow_null=True)
    local_name = validators.String(allow_null=True)
    class_name = validators.String(allow_null=True)
    subclass_name = validators.String(allow_null=True)
    geometry = validators.Object(allow_null=True)
    address = validators.Object(allow_null=True)
    blocks = BlocksValidator(allowed_blocks=BLOCKS_BY_VERBOSITY.get(LONG))

    def __init__(self, *args, **kwargs):
        if not args:
            if not self.PLACE_TYPE:
                raise Exception(
                    'Missing PLACE_TYPE in class %s',
                    self.__class__.__name__
                )
            kwargs['type'] = self.PLACE_TYPE
        super().__init__(*args, **kwargs)

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        raise NotImplementedError

    @classmethod
    def build_admins(cls, raw_admins):
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

    @classmethod
    def build_street(cls, raw_street):
        return {
            "id": raw_street.get("id"),
            "name": raw_street.get("name"),
            "label": raw_street.get("label"),
            "postcodes": raw_street.get("zip_codes")
        }

    @staticmethod
    def get_raw_address(es_place):
        return es_place.get("address") or {}

    @classmethod
    def get_raw_street(cls, es_place):
        raw_address = cls.get_raw_address(es_place)
        if raw_address.get('type') == 'street':
            return raw_address
        return raw_address.get("street") or {}

    @classmethod
    def get_raw_admins(cls, es_place):
        return es_place.get("administrative_regions") or []

    @classmethod
    def build_admin(cls, es_place, lang=None):
        return None

    @classmethod
    def get_postcodes(cls, es_place):
        return cls.get_raw_address(es_place).get("zip_codes")

    @classmethod
    def build_address(cls, es_place, lang):
        """
        Method to build the address field for an Address,
        a Street, an Admin or a POI.
        """
        raw_address = cls.get_raw_address(es_place)
        raw_street = cls.get_raw_street(es_place)
        raw_admins = cls.get_raw_admins(es_place)
        postcodes = cls.get_postcodes(es_place)
        if postcodes is not None:
            if isinstance(postcodes,list):
                postcodes = ';'.join(postcodes)

        id = raw_address.get("id")
        name = raw_address.get("name")
        housenumber = raw_address.get("house_number")
        label = raw_address.get("label")

        admins = cls.build_admins(raw_admins)
        street = cls.build_street(raw_street)

        return {
            "id": id,
            "name": name,
            "housenumber": housenumber,
            "postcode": postcodes,
            "label": label,
            "admin": cls.build_admin(es_place, lang),
            "street": street,
            "admins": admins
        }
