from elasticsearch import (
    Elasticsearch,
    ConnectionError,
    NotFoundError,
    ElasticsearchException,
)
import logging
from idunn import settings
from idunn.utils import prometheus
from idunn.utils.redis import RedisWrapper


logger = logging.getLogger(__name__)


class WikiEs:
    """
    Handle on an internal ElasticSearch populated with Wikipedia data.

    Note that the indexes are named f"wikidata_{lang}", but they still contain
    data from Wikipedia.
    """

    REDIS_INFO_KEY_PREFIX = "get_wiki_info"

    def __init__(self):
        wiki_es_url = settings.get("WIKI_ES")
        wiki_es_max_retries = settings.get("WIKI_ES_MAX_RETRIES")
        wiki_es_timeout = settings.get("WIKI_ES_TIMEOUT")

        if wiki_es_url is None:
            self.es = None
            return

        self.es = Elasticsearch(
            wiki_es_url,
            max_retries=wiki_es_max_retries,
            timeout=wiki_es_timeout,
        )

    def enabled(self):
        return self.es is not None

    @classmethod
    def is_lang_available(cls, lang):
        return lang in settings["ES_WIKI_LANG"].split(",")

    @classmethod
    def get_index(cls, lang):
        if cls.is_lang_available(lang):
            return f"wikidata_{lang}"
        return None

    def get_info(self, wikidata_id, lang):
        if not self.enabled() or not self.is_lang_available(lang):
            return None

        es_index = self.get_index(lang)

        def fetch_data():
            try:
                with prometheus.wiki_request_duration("wiki_es", "get_wiki_info"):
                    resp = (
                        self.es.search(
                            index=es_index,
                            body={
                                "query": {
                                    "bool": {"filter": {"term": {"wikibase_item": wikidata_id}}}
                                }
                            },
                        )
                        .get("hits", {})
                        .get("hits", [])
                    )
            except ConnectionError:
                logger.warning("Wiki ES not available: connection exception raised", exc_info=True)
                return None
            except NotFoundError:
                logger.warning(
                    "Wiki ES didn't find wikidata_id '%s' in wiki_index '%s'",
                    wikidata_id,
                    es_index,
                    exc_info=True,
                )
                return None
            except ElasticsearchException:
                logger.warning("Wiki ES failure: unknown elastic error", exc_info=True)
                return None

            if not resp:
                return None

            return resp[0].get("_source")

        redis_key = self.REDIS_INFO_KEY_PREFIX + "_" + wikidata_id + "_" + lang + "_" + es_index
        fetch_data_cached = RedisWrapper.cache_it(redis_key, fetch_data)
        return fetch_data_cached()


wiki_es = WikiEs()
