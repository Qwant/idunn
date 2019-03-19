from .place import Place
from idunn.api.utils import build_blocks, get_geom

class Admin(Place):
    PLACE_TYPE = 'admin'

    @classmethod
    def build_admin(cls, es_place, lang=None):
        labels = es_place.get('labels', {})
        return {
            'label': labels.get(lang) or es_place.get('label')
        }

    @classmethod
    def get_postcodes(cls, es_place):
        return es_place.get("zip_codes")

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        admin_addr = cls.build_address(es_place, lang)
        name = es_place.get('names', {}).get(lang) or es_place.get('name', '')

        return cls(
            id=es_place.get('id', ''),
            name=name,
            local_name=es_place.get('name', ''),
            class_name=es_place.get('zone_type'),
            subclass_name=es_place.get('zone_type'),
            geometry=get_geom(es_place),
            address=admin_addr,
            blocks=build_blocks(es_place, lang, verbosity)
        )
