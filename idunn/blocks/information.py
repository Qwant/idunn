from .base import BaseBlock, BlocksValidator

from idunn.blocks.services_and_information import ServicesAndInformationBlock
from idunn.blocks.wikipedia import WikipediaBlock

class InformationBlock(BaseBlock):
    BLOCK_TYPE = "information"

    blocks = BlocksValidator(allowed_blocks=[WikipediaBlock, ServicesAndInformationBlock])

    @classmethod
    def from_es(cls, es_poi, lang, prom):
        blocks = []

        wikipedia_block = WikipediaBlock.from_es(es_poi, lang, prom)
        services_block = ServicesAndInformationBlock.from_es(es_poi, lang, prom)

        if wikipedia_block is not None:
            blocks.append(wikipedia_block)
        if services_block is not None:
            blocks.append(services_block)

        if len(blocks) > 0:
            return cls(blocks=blocks)
