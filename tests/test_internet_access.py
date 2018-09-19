from app import app
from idunn.blocks.services_and_information import InternetAccessBlock

def test_internet_access_block():
    web_block = InternetAccessBlock.from_es(
        {
            "properties": {
                "wifi": "no"
            }
        },
        lang='en'
    )
    assert web_block is None


def test_internet_access_block_ok():
    web_block = InternetAccessBlock.from_es(
        {
            "properties": {
                "internet_access": "wlan"
            }
        },
        lang='en'
    )
    assert web_block == InternetAccessBlock(
        wifi=True
    )
