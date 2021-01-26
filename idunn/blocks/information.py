from .base import BaseBlock

from idunn.blocks.services_and_information import ServicesAndInformationBlock
from idunn.blocks.wikipedia import WikipediaBlock

from typing import List, Literal, Union


class InformationBlock(BaseBlock):
    type: Literal["information"] = "information"
    blocks: List[Union[WikipediaBlock, ServicesAndInformationBlock]]

    @classmethod
    def from_es(cls, place, lang):
        blocks = []
        wikipedia_block = WikipediaBlock.from_es(place, lang)
        services_block = ServicesAndInformationBlock.from_es(place, lang)

        if wikipedia_block is not None:
            blocks.append(wikipedia_block)
        if services_block is not None:
            blocks.append(services_block)

        if len(blocks) > 0:
            return cls(blocks=blocks)

        return None
