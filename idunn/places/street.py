from .place import Place
from idunn.api.utils import build_blocks, get_geom

class Street(Place):
    PLACE_TYPE = 'street'

    @classmethod
    def get_raw_street(cls, es_place):
        return es_place

    @classmethod
    def get_postcodes(cls, es_place):
        return es_place.get("zip_codes")

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        street_addr = cls.build_address(es_place, lang)

        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            local_name=es_place.get('name'),
            class_name='street',
            subclass_name='street',
            geometry=get_geom(es_place),
            address=street_addr,
            blocks=build_blocks(es_place, lang, verbosity)
        )
