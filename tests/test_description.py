from idunn.blocks.description import DescriptionBlock
from idunn.places import POI
from .utils import read_fixture


def orsay(lang=None):
    place = {"properties": {}}

    full = read_fixture("fixtures/orsay_museum.json")
    place["administrative_regions"] = full["administrative_regions"]

    key = f"description:{lang}" if lang else "description"
    place["properties"][key] = "Le musée d’Orsay est un musée national inauguré en 1986."

    return POI(place)


def test_description_block_with_lang():
    assert DescriptionBlock.from_es(orsay(lang="fr"), lang="en") is None
    assert DescriptionBlock.from_es(orsay(lang="fr"), lang="fr") == DescriptionBlock(
        type="description",
        description="Le musée d’Orsay est un musée national inauguré en 1986.",
        source="osm",
    )


def test_description_block_without_lang():
    assert DescriptionBlock.from_es(orsay(), lang="en") is None
    assert DescriptionBlock.from_es(orsay(), lang="fr") == DescriptionBlock(
        type="description",
        description="Le musée d’Orsay est un musée national inauguré en 1986.",
        source="osm",
    )
