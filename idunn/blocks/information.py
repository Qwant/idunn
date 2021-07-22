from .base import BaseBlock

from idunn.blocks.services_and_information import ServicesAndInformationBlock

from typing import List, Literal


class InformationBlock(BaseBlock):
    type: Literal["information"] = "information"
    blocks: List[ServicesAndInformationBlock]

    @classmethod
    def from_es(cls, place, lang):
        blocks = []
        services_block = ServicesAndInformationBlock.from_es(place, lang)

        if services_block is not None:
            blocks.append(services_block)

        if len(blocks) > 0:
            return cls(blocks=blocks)

        return None
