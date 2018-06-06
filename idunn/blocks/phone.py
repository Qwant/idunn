from apistar import types, validators

class PhoneBlock(types.Type):
    type = validators.String(default='phone')
    url = validators.String()
    international_format = validators.String()
    local_format = validators.String()

    @classmethod
    def from_es(cls, es_poi, lang):
        raw = es_poi.get('properties', {}).get('phone')
        if raw is None:
            raw = es_poi.get('properties', {}).get('contact:phone')
            if raw is None:
                return None
        
        return cls(
            url=f'tel:{raw}',
            international_format=raw,
            local_format=raw
        )
