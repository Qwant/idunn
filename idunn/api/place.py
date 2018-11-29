from apistar import types, validators

class Place(types.Type):
    PLACE_TYPE = ''

    type = validators.String()

    def __init__(self, *args, **kwargs):
        if not args:
            if not self.PLACE_TYPE:
                raise Exception(
                    'Missing PLACE_TYPE in class %s',
                    self.__class__.__name__
                )
            kwargs['type'] = self.PLACE_TYPE
        super().__init__(*args, **kwargs)

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        raise NotImplementedError

class Admin(Place):
    PLACE_TYPE = 'admin'

    id = validators.String(allow_null=True)
    name = validators.String(allow_null=True)
    label = validators.String(allow_null=True)

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            label=es_place.get('label', '')
        )

class Street(Place):
    PLACE_TYPE = 'street'

    id = validators.String(allow_null=True)
    name = validators.String(allow_null=True)
    label = validators.String(allow_null=True)

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            label=es_place.get('label', '')
        )

class Address(Place):
    PLACE_TYPE = 'address'

    id = validators.String(allow_null=True)
    name = validators.String(allow_null=True)
    label = validators.String(allow_null=True)

    @classmethod
    def load_place(cls, es_place, lang, settings, verbosity):
        return cls(
            id=es_place.get('id', ''),
            name=es_place.get('name', ''),
            label=es_place.get('label', '')
        )


