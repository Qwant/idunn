from idunn.blocks.phone import PhoneBlock
from idunn.places import POI


def test_phone_block():
    phone_block = PhoneBlock.from_es(POI({"properties": {"contact:phone": "tralala"}}), lang="en")
    assert phone_block is None

    phone_block = PhoneBlock.from_es(
        POI({"properties": {"contact:phone": "+33 1 40 20 52 29"}}), lang="en"
    )
    assert phone_block == PhoneBlock(
        url="tel:+33140205229",
        international_format="+33 1 40 20 52 29",
        local_format="01 40 20 52 29",
    )

    phone_block = PhoneBlock.from_es(
        POI(
            {
                "properties": {"contact:phone": "01 40 20 52 29"},
                "administrative_regions": [{"zone_type": "country", "country_codes": ["FR"]}],
            }
        ),
        lang="en",
    )
    assert phone_block == PhoneBlock(
        url="tel:+33140205229",
        international_format="+33 1 40 20 52 29",
        local_format="01 40 20 52 29",
    )
