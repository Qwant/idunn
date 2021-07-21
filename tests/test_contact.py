from idunn.blocks.contact import ContactBlock
from idunn.places import POI


def test_contact_block():
    contact_block = ContactBlock.from_es(
        POI({"properties": {"contact:email": "info@pershinghall.com"}}), lang="en"
    )

    assert contact_block == ContactBlock(
        url="mailto:info@pershinghall.com",
        email="info@pershinghall.com",
    )
