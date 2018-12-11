from apistar import types, validators
from idunn.blocks.base import BlocksValidator
from idunn.blocks import PhoneBlock, OpeningHourBlock, InformationBlock, WebSiteBlock, ContactBlock

LONG = "long"
SHORT = "short"
DEFAULT_VERBOSITY = LONG

BLOCKS_BY_VERBOSITY = {
    LONG: [
        OpeningHourBlock,
        PhoneBlock,
        InformationBlock,
        WebSiteBlock,
        ContactBlock
    ],
    SHORT: [
        OpeningHourBlock
    ]
}

class Place(types.Type):
    PLACE_TYPE = ''

    type = validators.String()
    id = validators.String(allow_null=True)
    name = validators.String(allow_null=True)
    local_name = validators.String(allow_null=True)
    class_name = validators.String(allow_null=True)
    subclass_name = validators.String(allow_null=True)
    geometry = validators.Object(allow_null=True)
    address = validators.Object(allow_null=True)
    blocks = BlocksValidator(allowed_blocks=BLOCKS_BY_VERBOSITY.get(LONG))

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
