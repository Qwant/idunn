from apistar import types, validators
from .base import BaseBlock, BlocksValidator

class AccessibilityBlock(BaseBlock):
    BLOCK_TYPE = "accessibility"

    wheelchair = validators.String(enum=['true', 'false', 'limited'])
    tactile_paving = validators.String(enum=['true', 'false', 'limited'])
    toilets_wheelchair = validators.String(enum=['true', 'false', 'limited'])

    @classmethod
    def from_es(cls, es_poi, lang):
        properties = es_poi.get('properties', {})

        raw_wheelchair = properties.get('wheelchair')
        raw_tactile_paving = properties.get('tactile_paving')
        raw_toilets_wheelchair = properties.get('toilets:wheelchair')

        if raw_wheelchair in ('yes', 'designated'):
            wheelchair = 'true'
        elif raw_wheelchair == 'limited':
            wheelchair = 'limited'
        else:
            wheelchair = 'false'

        if raw_tactile_paving == 'yes':
            tactile_paving = 'true'
        elif raw_tactile_paving in ('contrasted', 'primitive', 'incorrect'):
            tactile_paving = 'limited'
        else:
            tactile_paving = 'false'

        if raw_toilets_wheelchair == 'yes':
            toilets_wheelchair = 'true'
        else:
            toilets_wheelchair = 'false'

        return cls(
            wheelchair=wheelchair,
            tactile_paving=tactile_paving,
            toilets_wheelchair=toilets_wheelchair
        )

class InternetAccessBlock(BaseBlock):
    BLOCK_TYPE = "internet_access"

    wifi = validators.Boolean()

    @classmethod
    def from_es(cls, es_poi, lang):
        wifi = es_poi.get('properties', {}).get('wifi')

        if wifi is None:
            return None

        wifi = wifi in ('yes', '*', 'free')

        return cls(
            wifi=wifi
        )

class Beer(types.Type):
    name = validators.String()

class BreweryBlock(BaseBlock):
    BLOCK_TYPE = "brewery"

    beers = validators.Array(items=Beer)

    @classmethod
    def from_es(cls, es_poi, lang):
        brewery = es_poi.get('properties', {}).get('brewery')

        if brewery is None:
            return None

        beers = [Beer(name=b) for b in brewery.split(';')]

        return cls(
            beers=beers
        )

class ServicesAndInformationBlock(BaseBlock):
    BLOCK_TYPE = "services_and_information"

    blocks = BlocksValidator(allowed_blocks=[AccessibilityBlock, InternetAccessBlock, BreweryBlock])

    @classmethod
    def from_es(cls, es_poi, lang):
        blocks = []

        access_block = AccessibilityBlock.from_es(es_poi, lang)
        internet_block = InternetAccessBlock.from_es(es_poi, lang)
        brewery_block = BreweryBlock.from_es(es_poi, lang)

        if access_block is not None:
            blocks.append(access_block)
        if internet_block is not None:
            blocks.append(internet_block)
        if brewery_block is not None:
            blocks.append(brewery_block)

        if len(blocks) > 0:
            return cls(blocks=blocks)
