from .place import Place
from idunn.api.utils import build_blocks, get_geom, get_name


class POI(Place):
    PLACE_TYPE = 'poi'

    @classmethod
    def build_address(cls, es_place):
        raw_address = es_place.get('address', {})
        raw_admins = es_place.get('administrative_regions')
        if (raw_address, raw_admins) is not (None, None):
            raw_street = raw_address.get("street")
            street = None if raw_street is None else {
                "id": raw_street.get("id"),
                "name": raw_street.get("name"),
                "label": raw_street.get("label"),
                "postcode": raw_street.get("zip_codes")
            }
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
            postcode = raw_address.get("zip_codes")
            if postcode is not None:
                if isinstance(postcode,list):
                    postcode = ';'.join(postcode)
            return {
                "id": raw_address.get("id"),
                "name": raw_address.get("name"),
                "house_number": raw_address.get("house_number"),
                "label": raw_address.get("label"),
                "postcode": postcode,
                "street": street,
                "admins": admins
            }
        return None

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        properties = {p.get('key'): p.get('value') for p in es_place.get('properties')}
        es_place['properties'] = properties
        return cls.load_poi(es_place, lang, verbosity)

    @classmethod
    def load_poi(cls, es_poi, lang, verbosity):
        properties = es_poi.get('properties', {})
        raw_address = es_poi.get('address', {})
        admins = es_poi.get('administrative_regions', None)

        return cls(
            id=es_poi['id'],
            name=get_name(properties, lang),
            local_name=properties.get('name'),
            class_name=properties.get('poi_class'),
            subclass_name=properties.get('poi_subclass'),
            geometry=get_geom(es_poi),
            label=raw_address.get('label'),
            address=POI.build_address(es_poi),
            blocks=build_blocks(es_poi, lang, verbosity)
        )
