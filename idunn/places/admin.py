from .place import Place
from idunn.api.utils import build_blocks, get_geom, build_address

class Admin(Place):
    PLACE_TYPE = 'admin'

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        raw_address = es_place.get('address') or {}
        address = build_address(raw_address)

        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            local_name=es_place.get('name'),
            class_name='city',
            subclass_name='city',
            geometry=get_geom(es_place, 'polygon'),
            label=address.get('label'),
            address=address,
            blocks=build_blocks(es_place, lang, verbosity)
        )
