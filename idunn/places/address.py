from .place import Place
from idunn.api.utils import build_blocks, get_geom

class Address(Place):
    PLACE_TYPE = 'address'

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        address = es_place.get('address') or {}

        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            local_name=es_place.get('name'),
            class_name=es_place.get('poi_class'),
            subclass_name=es_place.get('poi_subclass'),
            geometry=get_geom(es_place, 'Point'),
            label=address.get('label'),
            address=address,
            blocks=build_blocks(es_place, lang, verbosity)
        )
