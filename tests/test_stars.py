from idunn.blocks.stars import StarsBlock, StarsDetails
from idunn.places import OsmPOI


def test_stars_block_invalid():
    stars_block = StarsBlock.from_es(
        OsmPOI({"properties": {"stars": "four stars"}, "id": "osm:way:154422021"}),
        lang="en",
    )
    assert stars_block is None


def test_stars_block_lodging():
    stars_block = StarsBlock.from_es(
        OsmPOI(
            {"properties": {"poi_class": "lodging", "stars": "4.5S"}, "id": "osm:way:154422021"}
        ),
        lang="en",
    )

    assert stars_block == StarsBlock(
        ratings=[
            StarsDetails(has_stars="yes", nb_stars=4.5, kind="lodging"),
        ]
    )


def test_stars_block_restaurant():
    stars_block = StarsBlock.from_es(
        OsmPOI({"properties": {"poi_class": "fast_food", "stars": "3"}, "id": "osm:way:154422021"}),
        lang="en",
    )

    assert stars_block == StarsBlock(
        ratings=[
            StarsDetails(has_stars="yes", nb_stars=3, kind="restaurant"),
        ]
    )
