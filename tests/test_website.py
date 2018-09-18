from app import app
from idunn.blocks.website import WebSiteBlock
from idunn.utils.prometheus import PrometheusTracker

def test_website_block():
    web_block = WebSiteBlock.from_es(
        {
            "properties": {
                "contact:website": "http://www.pershinghall.com"
            }
        },
        lang='en',
        prom=PrometheusTracker()
    )

    assert web_block == WebSiteBlock(
        url='http://www.pershinghall.com'
    )
