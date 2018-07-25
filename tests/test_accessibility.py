from app import app
from idunn.blocks.services_and_information import AccessibilityBlock

def test_accessibility_block():
    web_block = AccessibilityBlock.from_es(
        {
            "properties": {
                'wheelchair': 'limited',
                'tactile_paving': 'yes',
                'toilets:wheelchair': 'no'
            }
        },
        lang='en'
    )

    assert web_block == AccessibilityBlock(
        wheelchair='limited',
        tactile_paving='true',
        toilets_wheelchair='false'
    )


def test_accessibility_unknown():
    web_block = AccessibilityBlock.from_es(
        {
            "properties": {
                'wheelchair': 'toto',
                'tactile_paving': 'unknown',
            }
        },
        lang='en'
    )
    assert web_block is None
