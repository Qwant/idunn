from .place import Place
from idunn.api.utils import build_blocks, get_geom

class Address(Place):
    PLACE_TYPE = 'address'

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):

        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            local_name=es_place.get('name'),
            class_name='address',
            subclass_name='address',
            geometry=get_geom(es_place),
            label=es_place.get('label'),
            address=Place.build_address(es_place),
            blocks=build_blocks(es_place, lang, verbosity)
        )
