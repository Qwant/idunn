from .place import Place
from idunn.api.utils import build_blocks, get_geom

class Address(Place):
    PLACE_TYPE = 'address'

    @staticmethod
    def get_raw_address(es_place):
        return es_place

    @classmethod
    def get_raw_admins(cls, es_place):
        return cls.get_raw_street(es_place).get("administrative_regions") or []

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        address_addr = cls.build_address(es_place)

        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            local_name=es_place.get('name'),
            class_name='address',
            subclass_name='address',
            geometry=get_geom(es_place),
            address=address_addr,
            blocks=build_blocks(es_place, lang, verbosity)
        )
