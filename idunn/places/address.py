from .place import Place
from idunn.api.utils import build_blocks, get_geom

class Address(Place):
    PLACE_TYPE = 'address'

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        address_addr = Place.build_address(es_place)
        del address_addr['admin']

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
