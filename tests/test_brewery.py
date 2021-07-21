from idunn.blocks.services_and_information import BreweryBlock, Beer


def test_brewery_block():
    brewery_block = BreweryBlock.from_es(
        {"properties": {"brewery": "Tripel Karmeliet;Delirium;Chouffe"}}, lang="en"
    )

    assert brewery_block == BreweryBlock(
        beers=[Beer(name="Tripel Karmeliet"), Beer(name="Delirium"), Beer(name="Chouffe")]
    )
