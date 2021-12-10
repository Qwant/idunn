from idunn.blocks.delivery import DeliveryBlock
from idunn.places import POI


def test_delivery_block():
    delivery_block = DeliveryBlock.from_es(
        POI({"properties": {"delivery": "yes", "takeaway": "yes"}, "id": "osm:way:154422021"}),
        lang="en",
    )

    assert delivery_block == DeliveryBlock(
        click_and_collect="unknown",
        delivery="yes",
        takeaway="yes",
    )
