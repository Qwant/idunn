from pydantic import BaseModel, constr
from typing import ClassVar, List, Literal, Union

from .base import BaseBlock


class AccessibilityBlock(BaseBlock):
    STATUS_OK: ClassVar = "yes"
    STATUS_KO: ClassVar = "no"
    STATUS_LIMITED: ClassVar = "partial"
    STATUS_UNKNOWN: ClassVar = "unknown"

    type: Literal["accessibility"] = "accessibility"
    wheelchair: constr(
        regex="({})".format("|".join([STATUS_OK, STATUS_KO, STATUS_LIMITED, STATUS_UNKNOWN]))
    )
    toilets_wheelchair: constr(
        regex="({})".format("|".join([STATUS_OK, STATUS_KO, STATUS_LIMITED, STATUS_UNKNOWN]))
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

        if all(s == cls.STATUS_UNKNOWN for s in (wheelchair, toilets_wheelchair)):
            return None

        return cls(wheelchair=wheelchair, toilets_wheelchair=toilets_wheelchair)


class InternetAccessBlock(BaseBlock):
    type: Literal["internet_access"] = "internet_access"
    wifi: bool

    @classmethod
    def from_es(cls, es_poi, lang):
        properties = es_poi.get("properties", {})
        wifi = properties.get("wifi")
        internet_access = properties.get("internet_access")

        has_wifi = wifi in ("yes", "free") or internet_access in ("wlan", "wifi", "yes")

        if not has_wifi:
            return None

        return cls(wifi=has_wifi)


class Beer(BaseModel):
    name: str


class BreweryBlock(BaseBlock):
    type: Literal["brewery"] = "brewery"
    beers: List[Beer]

    @classmethod
    def from_es(cls, es_poi, lang):
        brewery = es_poi.get("properties", {}).get("brewery")

        if brewery is None:
            return None

        beers = [Beer(name=b) for b in brewery.split(";")]

        return cls(beers=beers)


def get_diet_status(diet_kind, data):
    info = data.get("properties", {}).get("diet:{}".format(diet_kind))
    return {
        CuisineBlock.STATUS_YES: CuisineBlock.STATUS_YES,
        CuisineBlock.STATUS_NO: CuisineBlock.STATUS_NO,
        CuisineBlock.STATUS_ONLY: CuisineBlock.STATUS_ONLY,
    }.get(info, CuisineBlock.STATUS_UNKNOWN)


class Cuisine(BaseModel):
    name: str


class CuisineBlock(BaseBlock):
    SUPPORTED_DIETS: ClassVar = ("vegetarian", "vegan", "gluten_free")
    STATUS_YES: ClassVar = "yes"
    STATUS_NO: ClassVar = "no"
    STATUS_ONLY: ClassVar = "only"
    STATUS_UNKNOWN: ClassVar = "unknown"

    type: Literal["cuisine"] = "cuisine"
    cuisines: List[Cuisine]
    vegetarian: str
    vegan: str
    gluten_free: str

    @classmethod
    def from_es(cls, es_poi, lang):
        cuisine = es_poi.get("properties", {}).get("cuisine")

        vegetarian = get_diet_status("vegetarian", es_poi)
        vegan = get_diet_status("vegan", es_poi)
        gluten_free = get_diet_status("gluten_free", es_poi)

        cuisines = []
        if cuisine is not None:
            cuisines = [Cuisine(name=b) for b in cuisine.split(";")]
        elif (
            vegetarian == cls.STATUS_UNKNOWN
            and vegan == cls.STATUS_UNKNOWN
            and gluten_free == cls.STATUS_UNKNOWN
        ):
            return None

        return cls(cuisines=cuisines, vegetarian=vegetarian, vegan=vegan, gluten_free=gluten_free)


class ServicesAndInformationBlock(BaseBlock):
    type: Literal["services_and_information"] = "services_and_information"
    blocks: List[Union[AccessibilityBlock, InternetAccessBlock, BreweryBlock, CuisineBlock]]

    @classmethod
    def from_es(cls, es_poi, lang):
        blocks = []
        access_block = AccessibilityBlock.from_es(es_poi, lang)
        internet_block = InternetAccessBlock.from_es(es_poi, lang)
        brewery_block = BreweryBlock.from_es(es_poi, lang)
        cuisine_block = CuisineBlock.from_es(es_poi, lang)

        if access_block is not None:
            blocks.append(access_block)
        if internet_block is not None:
            blocks.append(internet_block)
        if brewery_block is not None:
            blocks.append(brewery_block)
        if cuisine_block is not None:
            blocks.append(cuisine_block)

        if len(blocks) > 0:
            return cls(blocks=blocks)

        return None
