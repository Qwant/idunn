import logging
from typing import Literal

from idunn import settings
from idunn.datasources.wiki_es import wiki_es
from idunn.datasources.wikipedia import wikipedia_session
from .base import BaseBlock


logger = logging.getLogger(__name__)


def limit_size(content: str) -> str:
    wiki_desc_max_size = int(settings["WIKI_DESC_MAX_SIZE"])

    if len(content) > wiki_desc_max_size:
        return content[:wiki_desc_max_size] + "…"

    return content


# TODO: this block should not be used, the block `description` is instead favored.
class WikipediaBlock(BaseBlock):
    type: Literal["wikipedia"] = "wikipedia"
    url: str
    title: str
    description: str

    @classmethod
    def from_es(cls, place, lang):
        # If `wikidata_id` is present and `lang` is available in `wiki_es`, try
        # to fetch from ES.
        if place.wikidata_id is not None and wiki_es.enabled() and wiki_es.is_lang_available(lang):
            wiki_poi_info = wiki_es.get_info(place.wikidata_id, lang)

            if wiki_poi_info is None:
                return None

            return cls(
                url=wiki_poi_info.get("url"),
                title=wiki_poi_info.get("title")[0],
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
            title=wiki_summary.get("displaytitle", ""),
            description=limit_size(wiki_summary.get("extract", "")),
        )
