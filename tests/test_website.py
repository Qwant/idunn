from idunn.blocks.website import WebSiteBlock
from idunn.places import POI


def test_website_block():
    web_block = WebSiteBlock.from_es(
        POI(
            {
                "properties": {"contact:website": "http://www.pershinghall.com"},
                "id": "osm:way:154422021",
            }
        ),
        lang="en",
    )

    assert web_block == WebSiteBlock(
        url="http://www.pershinghall.com",
        label="www.pershinghall.com",
    )
