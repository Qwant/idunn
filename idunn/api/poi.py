from apistar import types, validators
from idunn.blocks.phone import PhoneBlock
from idunn.blocks.opening_hour import OpeningHourBlock

BLOCKS_ORDER = [
    OpeningHourBlock,
    PhoneBlock
]

def build_blocks(es_poi, lang):
    blocks = []
    for c in BLOCKS_ORDER:
        block = c.from_es(es_poi, lang)
        if block is not None:
            blocks.append(block)
    return blocks

def get_name(properties, lang):
    """Return the POI name from the properties field of the elastic response
    Here 'name' corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

    If lang is None or if name:lang is not in the properties
    Then name receives the local name value

    'local_name' corresponds to the name in the language of the country where the POI is located.

    >>> get_name({}, 'fr') is None
    True

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, None)
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'cz')
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'fr')
    'spontinifr'
    """
    name = properties.get(f'name:{lang}')
    if name is None:
        name = properties.get('name')
    return name

def get_geom(es_poi):
    """Return the correct geometry from the elastic response

    A correct geometry means both lat and lon coordinates are required

    >>> get_geom({}) is None
    True

    >>> get_geom({'coord':{"lon": None, "lat": 48.858260156496016}}) is None
    True

    >>> get_geom({'coord':{"lon": 2.2944990157640612, "lat": None}}) is None
    True

    >>> get_geom({'coord':{"lon": 2.2944990157640612, "lat": 48.858260156496016}})
    {'coordinates': [2.2944990157640612, 48.858260156496016], 'type': 'Point'}
    """
    geom = None
    if 'coord' in es_poi:
        coord = es_poi.get('coord')
        lon = coord.get('lon')
        lat = coord.get('lat')
        if lon is not None and lat is not None:
            geom = {
                'coordinates': [lon, lat],
                'type': 'Point'
            }
    return geom

class POI(types.Type):
    id = validators.String(allow_null=True)
    name = validators.String(allow_null=True)
    local_name = validators.String(allow_null=True)
    class_name = validators.String(allow_null=True)
    subclass_name = validators.String(allow_null=True)
    geometry = validators.Object(allow_null=True)
    address = validators.Object(allow_null=True)
    blocks = validators.Array()

    @classmethod
    def load_poi(cls, es_poi, lang):

        properties = es_poi.get('properties', {})
        address = es_poi.get('address') or {}

        return cls(
            id=es_poi['id'],
            name=get_name(properties, lang),
            local_name=properties.get('name'),
            class_name=properties.get('poi_class'),
            subclass_name=properties.get('poi_subclass'),
            geometry=get_geom(es_poi),
            address= {
                'label': address.get('label')
            },
            blocks=build_blocks(es_poi, lang)
        )
