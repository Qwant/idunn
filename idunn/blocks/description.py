from enum import Enum
from typing import Literal, Optional

import idunn
from idunn import settings
from idunn.datasources.wiki_es import wiki_es
from idunn.datasources.wikipedia import wikipedia_session
from .base import BaseBlock


def limit_size(content: str) -> str:
    desc_max_size = int(settings["DESC_MAX_SIZE"])

    if len(content) > desc_max_size:
        return content[:desc_max_size] + "…"

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
    def from_wikipedia(cls, place, lang):
        """
        Attempt to fetch wikipedia description, by using internal elasticsearch
        database or directly from Wikipedia's if it is not available.
        """
        # Try to fetch from ES.
        if place.wikidata_id is not None and wiki_es.enabled() and wiki_es.is_lang_available(lang):
            wiki_poi_info = wiki_es.get_info(place.wikidata_id, lang)

            if wiki_poi_info is None:
                return None

            return cls(
                url=wiki_poi_info.get("url"),
                source=DescriptionSources.WIKIPEDIA,
                description=limit_size(wiki_poi_info.get("content", "")),
            )

        # Overwise, fetch summary from Wikipedia API
        wikipedia_value = place.properties.get("wikipedia")
        wiki_title = None

        if not wikipedia_value:
            return None

        wiki_split = wikipedia_value.split(":", maxsplit=1)

        if len(wiki_split) != 2:
            return None

        wiki_lang, wiki_title = wiki_split
        wiki_lang = wiki_lang.lower()

        if wiki_lang != lang:
            wiki_title = wikipedia_session.get_title_in_language(wiki_title, wiki_lang, lang)

        if not wiki_title:
            return None

        wiki_summary = wikipedia_session.get_summary(wiki_title, lang)

        if not wiki_summary:
            return None

        return cls(
            url=wiki_summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
            source=DescriptionSources.WIKIPEDIA,
            description=limit_size(wiki_summary.get("extract", "")),
        )

    @classmethod
    def from_es(cls, place, lang):
        if block := cls.from_wikipedia(place, lang):
            return block

        description = place.get_description(lang)

        if not description:
            return None

        source = (
            DescriptionSources.PAGESJAUNES
            if isinstance(place, idunn.places.PjApiPOI)
            else DescriptionSources.OSM
        )

        return cls(
            description=limit_size(description),
            source=source,
            url=place.get_description_url(lang),
        )
