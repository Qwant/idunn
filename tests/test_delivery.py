from idunn.blocks.delivery import DeliveryBlock
from idunn.places import POI


def test_website_block():
    web_block = DeliveryBlock.from_es(
        POI({"properties": {"delivery": "yes", "takeaway": "yes"}}), lang="en"
    )

    assert web_block == DeliveryBlock(available=["delivery", "takeaway"])
