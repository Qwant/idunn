from apistar import types, validators
from .base import BaseBlock, BlocksValidator


class AccessibilityBlock(BaseBlock):
    BLOCK_TYPE = "accessibility"

    STATUS_OK = "yes"
    STATUS_KO = "no"
    STATUS_LIMITED = "partial"
    STATUS_UNKNOWN = "unknown"

    wheelchair = validators.String(
        enum=[STATUS_OK, STATUS_KO, STATUS_LIMITED, STATUS_UNKNOWN]
    )
    toilets_wheelchair = validators.String(
        enum=[STATUS_OK, STATUS_KO, STATUS_LIMITED, STATUS_UNKNOWN]
    )

    @classmethod
    def from_es(cls, es_poi, lang):
        properties = es_poi.get("properties", {})

        raw_wheelchair = es_poi.get_raw_wheelchair()
        raw_toilets_wheelchair = properties.get("toilets:wheelchair")

        if raw_wheelchair in ("yes", "designated", True):
            wheelchair = cls.STATUS_OK
        elif raw_wheelchair == "limited":
            wheelchair = cls.STATUS_LIMITED
        elif raw_wheelchair in ("no", False):
            wheelchair = cls.STATUS_KO
        else:
            wheelchair = cls.STATUS_UNKNOWN

        if raw_toilets_wheelchair in ("yes", True):
            toilets_wheelchair = cls.STATUS_OK
        elif raw_toilets_wheelchair == "limited":
            toilets_wheelchair = cls.STATUS_LIMITED
        elif raw_toilets_wheelchair in ("no", False):
            toilets_wheelchair = cls.STATUS_KO
        else:
            toilets_wheelchair = cls.STATUS_UNKNOWN

        if all(
            s == cls.STATUS_UNKNOWN
            for s in (wheelchair, toilets_wheelchair)
        ):
            return None

        return cls(
            wheelchair=wheelchair,
            toilets_wheelchair=toilets_wheelchair,
        )


class InternetAccessBlock(BaseBlock):
    BLOCK_TYPE = "internet_access"

    wifi = validators.Boolean()

    @classmethod
    def from_es(cls, es_poi, lang):
        properties = es_poi.get("properties", {})
        wifi = properties.get("wifi")
        internet_access = properties.get("internet_access")

        has_wifi = wifi in ("yes", "free") or internet_access in ("wlan", "wifi", "yes")

        if not has_wifi:
            return None

        return cls(wifi=has_wifi)


class Beer(types.Type):
    name = validators.String()


class BreweryBlock(BaseBlock):
    BLOCK_TYPE = "brewery"

    beers = validators.Array(items=Beer)

    @classmethod
    def from_es(cls, es_poi, lang):
        brewery = es_poi.get("properties", {}).get("brewery")

        if brewery is None:
            return None

        beers = [Beer(name=b) for b in brewery.split(";")]

        return cls(beers=beers)


class ServicesAndInformationBlock(BaseBlock):
    BLOCK_TYPE = "services_and_information"

    blocks = BlocksValidator(
        allowed_blocks=[AccessibilityBlock, InternetAccessBlock, BreweryBlock]
    )

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
