from enum import Enum
from typing import Literal, Optional

import idunn
from idunn import settings
from idunn.blocks.wikipedia import WikipediaBlock
from .base import BaseBlock

DESC_MAX_SIZE = int(settings["DESC_MAX_SIZE"])


def limit_size(content: str) -> str:
    if len(content) > DESC_MAX_SIZE:
        return content[:DESC_MAX_SIZE] + "…"

    return content


class DescriptionSources(Enum):
    OSM = "osm"
    PAGESJAUNES = "pagesjaunes"
    WIKIPEDIA = "wikipedia"


class DescriptionBlock(BaseBlock):
    type: Literal["description"] = "description"
    description: str
    source: DescriptionSources
    url: Optional[str]

    @classmethod
    def from_es(cls, place, lang):
        if wiki_block := WikipediaBlock.from_es(place, lang):
            return cls(
                description=limit_size(wiki_block.description),
                source=DescriptionSources.WIKIPEDIA,
                url=wiki_block.url,
            )

        if description := place.get_description(lang):
            if isinstance(place, idunn.places.PjApiPOI):
                source = DescriptionSources.PAGESJAUNES
            else:
                source = DescriptionSources.OSM

            return cls(
                description=limit_size(description),
                source=source,
                url=place.get_description_url(lang),
            )

        return None
