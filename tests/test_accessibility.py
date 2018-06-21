from app import app
from idunn.blocks.services_and_information import AccessibilityBlock

def test_accessibility_block():
    web_block = AccessibilityBlock.from_es(
        {
            "properties": {
                'wheelchair': 'yes',
                'tactile_paving': 'incorrect',
                'toilets_wheelchair': 'no'
            }
        },
        lang='en'
    )

    assert web_block == AccessibilityBlock(
        wheelchair='true',
        tactile_paving='limited',
        toilets_wheelchair='false'
    )
