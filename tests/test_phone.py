from idunn.blocks.phone import PhoneBlock
from idunn.places import POI


def test_phone_block_invalid():
    phone_block = PhoneBlock.from_es(
        POI({"properties": {"contact:phone": "tralala"}, "id": "osm:way:154422021"}), lang="en"
    )
    assert phone_block is None


def test_phone_block_international():
    phone_block = PhoneBlock.from_es(
        POI({"properties": {"contact:phone": "+33 1 40 20 52 29"}, "id": "osm:way:154422021"}),
        lang="en",
    )
    assert phone_block == PhoneBlock(
        url="tel:+33140205229",
        international_format="+33 1 40 20 52 29",
        local_format="01 40 20 52 29",
    )


def test_phone_block_national():
    phone_block = PhoneBlock.from_es(
        POI(
            {
                "id": "osm:way:154422021",
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


def test_phone_block_multiple_numbers():
    phone_block = PhoneBlock.from_es(
        POI(
            {
                "id": "osm:way:154422021",
                "properties": {"contact:phone": "01 40 20 52 29 ; 01 99 99 99 99"},
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
