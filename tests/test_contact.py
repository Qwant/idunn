from app import app
from idunn.blocks.contact import ContactBlock
from idunn.utils.prometheus import PrometheusTracker

def test_contact_block():
    web_block = ContactBlock.from_es(
        {
            "properties": {
                "contact:email": "info@pershinghall.com"
            }
        },
        lang='en',
        prom=PrometheusTracker()
    )

    assert web_block == ContactBlock(
        url='mailto:info@pershinghall.com'
    )
