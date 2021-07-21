from idunn.blocks.services_and_information import InternetAccessBlock


def test_internet_access_block():
    internet_access_block = InternetAccessBlock.from_es({"properties": {"wifi": "no"}}, lang="en")
    assert internet_access_block is None


def test_internet_access_block_ok():
    internet_access_block = InternetAccessBlock.from_es(
        {"properties": {"internet_access": "wlan"}}, lang="en"
    )
    assert internet_access_block == InternetAccessBlock(wifi=True)
