from apistar import types, validators

class BaseBlock(types.Type):
    BLOCK_TYPE = '' # To override in each subclass

    type = validators.String()

    def __init__(self, *args, **kwargs):
        if not args:
            if not self.BLOCK_TYPE:
                raise Exception(
                    'Missing BLOCK_TYPE in class %s',
                    self.__class__.__name__
                )
            kwargs['type'] = self.BLOCK_TYPE
        super().__init__(*args, **kwargs)

    @classmethod
    def from_es(cls, es_poi, lang):
        raise NotImplementedError

    @classmethod
    def is_enabled(cls):
        return True


class TypedBlockValidator(validators.Object):
    errors = {
        'missing_type': 'Must have a non-empty type',
        'unknown_type': 'Block must have a valid type',
        'not_allowed_block': 'Must be one of these allowed blocks: {allowed_blocks}'
    }

    def __init__(self, *args, **kwargs):
        self.allowed_blocks = set(kwargs.pop('allowed_blocks', {}))
        super().__init__(*args, **kwargs)

    def validate(self, value, definitions=None, allow_coerce=False):
        from . import BLOCK_TYPE_TO_CLASS

        block_type = value.get('type')
        if not block_type:
            self.error('missing_type', value)

        block_class = BLOCK_TYPE_TO_CLASS.get(block_type)
        if block_class is None:
            self.error('unknown_type', value)
        if self.allowed_blocks and block_class not in self.allowed_blocks:
            self.error('not_allowed_block', value)

        return block_class.validate(value=value, definitions=definitions,
                                    allow_coerce=allow_coerce)


class BlocksValidator(validators.Array):
    def __init__(self, *args, **kwargs):
        allowed_blocks = kwargs.pop('allowed_blocks', [])
        assert not kwargs.get('items'), "'items' should not be passed to BlocksValidator"
        kwargs['items'] = TypedBlockValidator(allowed_blocks=allowed_blocks)
        super().__init__(*args, **kwargs)
