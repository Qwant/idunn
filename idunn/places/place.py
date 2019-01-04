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
    def build_address(cls, es_place):
        raw_address = es_place.get('address') or {}
        raw_street = es_place.get('street') or raw_address.get("street") or {}
        raw_admins = es_place.get('administrative_regions') or raw_street.get('administrative_regions') or raw_address.get('administrative_regions') or {}

        admins = []
        if not raw_admins is None:
            for raw_admin in raw_admins:
                admin = {
                    "id": raw_admin.get("id"),
                    "label": raw_admin.get("label"),
                    "name": raw_admin.get("name"),
                    "level": raw_admin.get("level"),
                    "postcode": raw_admin.get("zip_codes")
                }
                admins.append(admin)
        postcodes = es_place.get("zip_codes") or raw_address.get("zip_codes")
        if postcodes is not None:
            if isinstance(postcodes,list):
                postcodes = ';'.join(postcodes)
        return {
            "id": raw_address.get("id"),
            "name": raw_address.get("name"),
            "housenumber": raw_address.get("house_number"),
            "postcode": postcodes,
            "admin": {
                "label": es_place.get("label")
            },
            "street": {
                "id": raw_street.get("id"),
                "name": raw_street.get("name"),
                "label": raw_street.get("label"),
                "postcodes": raw_street.get("zip_codes")
            },
            "admins": admins
        }
