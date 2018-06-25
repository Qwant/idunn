from app import app
from idunn.blocks.contact import ContactBlock

def test_contact_block():
    web_block = ContactBlock.from_es(
        {
            "properties": {
                "contact:email": "info@pershinghall.com"
            }
        },
        lang='en'
    )

    assert web_block == ContactBlock(
        url='mailto:info@pershinghall.com'
    )
