from .base import BaseBlock, BlocksValidator

from idunn.blocks.services_and_information import ServicesAndInformationBlock
from idunn.blocks.wikipedia import WikipediaBlock

from typing import ClassVar


class InformationBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "information"

    blocks: ClassVar = BlocksValidator(
        allowed_blocks=[WikipediaBlock, ServicesAndInformationBlock]
    )

    @classmethod
    def from_es(cls, es_poi, lang):
        blocks = []

        wikipedia_block = WikipediaBlock.from_es(es_poi, lang)
        services_block = ServicesAndInformationBlock.from_es(es_poi, lang)

        if wikipedia_block is not None:
            blocks.append(wikipedia_block)
        if services_block is not None:
            blocks.append(services_block)

        if len(blocks) > 0:
            return cls(blocks=blocks)
