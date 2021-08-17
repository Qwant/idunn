from idunn.blocks.stars import StarsBlock, StarsDetails
from idunn.places import POI


def test_stars_block_invalid():
    stars_block = StarsBlock.from_es(
        POI({"properties": {"stars": "four stars"}}),
        lang="en",
    )
    assert stars_block is None


def test_stars_block_lodging():
    stars_block = StarsBlock.from_es(
        POI({"properties": {"poi_class": "lodging", "stars": "4.5S"}}),
        lang="en",
    )

    assert stars_block == StarsBlock(
        ratings=[
            StarsDetails(has_stars="yes", nb_stars=4.5, kind="lodging"),
        ]
    )


def test_stars_block_restaurant():
    stars_block = StarsBlock.from_es(
        POI({"properties": {"poi_class": "fast_food", "stars": "3"}}),
        lang="en",
    )

    assert stars_block == StarsBlock(
        ratings=[
            StarsDetails(has_stars="yes", nb_stars=3, kind="restaurant"),
        ]
    )
