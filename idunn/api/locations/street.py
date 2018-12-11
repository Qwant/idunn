from idunn.api.place import Place
from idunn.utils.geom import build_blocks, get_geom

class Street(Place):
    PLACE_TYPE = 'street'

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        address = es_place.get('address') or {}

        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            local_name=es_place.get('name'),
            class_name=es_place.get('poi_class'),
            subclass_name=es_place.get('poi_subclass'),
            geometry=get_geom(es_place),
            address= {
                'label': address.get('label')
            },
            blocks=build_blocks(es_place, lang, verbosity)
        )
