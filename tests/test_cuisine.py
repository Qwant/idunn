from app import app
from idunn.blocks.services_and_information import CuisineBlock, Cuisine


def test_cuisine_block():
    web_block = CuisineBlock.from_es({"properties": {"cuisine": "Italian;French"}}, lang="en")

    assert web_block == CuisineBlock(
        cuisines=[Cuisine(name="Italian"), Cuisine(name="French")],
        vegetarian=CuisineBlock.STATUS_UNKNOWN,
        vegan=CuisineBlock.STATUS_UNKNOWN,
        gluten_free=CuisineBlock.STATUS_UNKNOWN,
    )
