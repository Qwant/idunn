from app import app
from idunn.blocks.services_and_information import BreweryBlock, Beer


def test_internet_access_block():
    web_block = BreweryBlock.from_es(
        {"properties": {"brewery": "Tripel Karmeliet;Delirium;Chouffe"}}, lang="en"
    )

    assert web_block == BreweryBlock(
        beers=[Beer(name="Tripel Karmeliet"), Beer(name="Delirium"), Beer(name="Chouffe")]
    )
