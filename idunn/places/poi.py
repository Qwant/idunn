from .place import Place
from idunn.api.utils import build_blocks, get_geom, get_name

class POI(Place):
    PLACE_TYPE = 'poi'

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        properties = {p.get('key'): p.get('value') for p in es_place.get('properties')}
        es_place['properties'] = properties
        return cls.load_poi(es_place, lang, verbosity)

    @classmethod
    def load_poi(cls, es_poi, lang, verbosity):
        properties = es_poi.get('properties', {})
        address = es_poi.get('address') or {}

        return cls(
            id=es_poi['id'],
            name=get_name(properties, lang),
            local_name=properties.get('name'),
            class_name=properties.get('poi_class'),
            subclass_name=properties.get('poi_subclass'),
            geometry=get_geom(es_poi, 'Point'),
            label=address.get('label'),
            address=address,
            blocks=build_blocks(es_poi, lang, verbosity)
        )
