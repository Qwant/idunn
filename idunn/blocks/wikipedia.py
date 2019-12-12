import json
import logging
import requests
import pybreaker
from requests.exceptions import HTTPError, RequestException, Timeout
from redis import Redis, RedisError

from idunn import settings
from idunn.utils import prometheus
from idunn.utils.redis import get_redis_pool, RedisNotConfigured
from idunn.utils.circuit_breaker import IdunnCircuitBreaker
from idunn.utils.rate_limiter import IdunnRateLimiter, TooManyRequestsException
from .base import BaseBlock

from typing import ClassVar


GET_WIKI_INFO = "get_wiki_info"
GET_TITLE_IN_LANGUAGE = "get_title_in_language"
GET_SUMMARY = "get_summary"

DISABLED_STATE = object() # Used to flag cache as disabled by settings

logger = logging.getLogger(__name__)


class WikiUndefinedException(Exception):
    pass


class CacheNotAvailable(Exception):
    pass


class WikipediaCache:
    _expire = None
    _connection = None

    @classmethod
    def set_value(cls, key, json_result):
        try:
            cls._connection.set(key, json_result, ex=cls._expire)
        except RedisError:
            prometheus.exception("RedisError")
            logging.exception("Got a RedisError")

    @classmethod
    def get_value(cls, key):
        try:
            value_stored = cls._connection.get(key)
            return value_stored
        except RedisError as exc:
            prometheus.exception("RedisError")
            logging.exception("Got a RedisError")
            raise CacheNotAvailable from exc

    @classmethod
    def init_cache(cls):
        cls._expire = int(settings['WIKI_CACHE_TIMEOUT'])  # seconds
        redis_db = settings['WIKI_CACHE_REDIS_DB']
        try:
            redis_pool = get_redis_pool(db=redis_db)
        except RedisNotConfigured:
            logger.warning("No Redis URL has been set for caching", exc_info=True)
            cls._connection = DISABLED_STATE
        else:
            cls._connection = Redis(connection_pool=redis_pool)

    @classmethod
    def cache_it(cls, key, f):
        """
        Takes function f and put its result in a redis cache.
        It requires a prefix string to identify the name
        of the function cached.
        """
        if WikipediaCache._connection is None:
            WikipediaCache.init_cache()

        def with_cache(*args, **kwargs):
            """
            If the redis is up we use the cache,
            otherwise we bypass it
            """
            if cls._connection is not DISABLED_STATE:
                try:
                    value_stored = cls.get_value(key)
                except CacheNotAvailable:
                    # Cache is not reachable: we don't want to execute 'f'
                    # (and fetch wikipedia content, possibly very often)
                    return None
                if value_stored is not None:
                    return json.loads(value_stored.decode('utf-8'))
                result = f(*args, **kwargs)
                json_result = json.dumps(result)
                cls.set_value(key, json_result)
                return result
            return f(*args, **kwargs)
        return with_cache

    @classmethod
    def disable(cls):
        cls._connection = DISABLED_STATE


class WikipediaSession:
    _session = None
    _rate_limiter = None
    timeout = 1. # seconds

    API_V1_BASE_PATTERN = "https://{lang}.wikipedia.org/api/rest_v1"
    API_PHP_BASE_PATTERN = "https://{lang}.wikipedia.org/w/api.php"

    circuit_breaker = IdunnCircuitBreaker(name='wikipedia_api_breaker')

    class Helpers:
        @staticmethod
        def handle_requests_error(f):
            def wrapped_f(*args, **kwargs):
                try:
                    with WikipediaSession.get_rate_limiter().limit(client='idunn') as limit:
                        return f(*args, **kwargs)
                except pybreaker.CircuitBreakerError:
                    prometheus.exception("CircuitBreakerError")
                    logger.error("Got CircuitBreakerError in {}".format(f.__name__), exc_info=True)
                except HTTPError:
                    prometheus.exception("HTTPError")
                    logger.warning("Got HTTP error in {}".format(f.__name__), exc_info=True)
                except Timeout:
                    prometheus.exception("RequestsTimeout")
                    logger.warning("External API timed out in {}".format(f.__name__), exc_info=True)
                except RequestException:
                    prometheus.exception("RequestException")
                    logger.error("Got Request exception in {}".format(f.__name__), exc_info=True)
                except TooManyRequestsException:
                    prometheus.exception("TooManyRequests")
                    logger.warning("Got TooManyRequests{}".format(f.__name__), exc_info=True)
                except RedisError:
                    prometheus.exception("RedisError")
                    logger.warning("Got redis ConnectionError{}".format(f.__name__), exc_info=True)
            return wrapped_f

    @property
    def session(self):
        if self._session is None:
            user_agent = settings['WIKI_USER_AGENT']
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": user_agent})
        return self._session

    @classmethod
    def get_rate_limiter(cls):
        if cls._rate_limiter is None:
            cls._rate_limiter = IdunnRateLimiter(
                resource='WikipediaAPI',
                max_requests=int(settings['WIKI_API_RL_MAX_CALLS']),
                expire=int(settings['WIKI_API_RL_PERIOD'])
            )
        return cls._rate_limiter

    @Helpers.handle_requests_error
    @circuit_breaker
    def get_summary(self, title, lang):
        url = "{base_url}/page/summary/{title}".format(
            base_url=self.API_V1_BASE_PATTERN.format(lang=lang), title=title
        )

        with prometheus.wiki_request_duration("wiki_api", "get_summary"):
            resp = self.session.get(
                url=url,
                params={"redirect": True},
                timeout=self.timeout
            )

        resp.raise_for_status()
        return resp.json()

    @Helpers.handle_requests_error
    @circuit_breaker
    def get_title_in_language(self, title, source_lang, dest_lang):
        url = self.API_PHP_BASE_PATTERN.format(lang=source_lang)

        with prometheus.wiki_request_duration("wiki_api", "get_title"):
            resp = self.session.get(
                url=url,
                params={
                    "action": "query",
                    "prop": "langlinks",
                    "titles": title,
                    "lllang": dest_lang,
                    "formatversion": 2,
                    "format": "json",
                },
                timeout=self.timeout,
            )

        resp.raise_for_status()
        resp_data = resp.json()
        resp_pages = resp_data.get("query", {}).get("pages", [])
        if len(resp_pages) > 0:
            if len(resp_pages) > 1:
                logger.warning(
                    "Got multiple pages in wikipedia langlinks response: %s", resp_data
                )
            lang_links = resp_pages[0].get("langlinks", [])
            if len(lang_links) > 0:
                return lang_links[0].get("title")

        return None

class SizeLimiter:
    @classmethod
    def limit_size(cls, content):
        """
        Just cut a string if its length > max_size
        """
        max_wiki_desc_size = settings['WIKI_DESC_MAX_SIZE']
        return (content[:max_wiki_desc_size] + '...') if len(content) > max_wiki_desc_size else content


class WikipediaBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "wikipedia"

    url: str
    title: str
    description: str

    _wiki_session: ClassVar = WikipediaSession()

    @classmethod
    def from_es(cls, es_poi, lang):
        """
        If "wikidata_id" is present and "lang" is in "ES_WIKI_LANG",
        then we try to fetch our "WIKI_ES" (if WIKI_ES has been defined),
        else then we fetch the wikipedia API.
        """
        wikidata_id = es_poi.wikidata_id
        if wikidata_id is not None:
            wiki_index = es_poi.get_wiki_index(lang)
            if wiki_index is not None:
                try:
                    key = GET_WIKI_INFO + "_" + wikidata_id + "_" + lang + "_" + wiki_index
                    wiki_poi_info = WikipediaCache.cache_it(key, es_poi.get_wiki_info)(wikidata_id, wiki_index)
                    if wiki_poi_info is not None:
                        return cls(
                            url=wiki_poi_info.get("url"),
                            title=wiki_poi_info.get("title")[0],
                            description=SizeLimiter.limit_size(wiki_poi_info.get("content", "")),
                        )
                    else:
                        """
                        if the lang is in ES_WIKI_LANG and
                        the WIKI_ES contains no information,
                        then there is no need to call the
                        Wikipedia API, i.e we return None
                        """
                        return None
                except WikiUndefinedException:
                    logger.info("WIKI_ES variable has not been set: call to Wikipedia")

        wikipedia_value = es_poi.properties.get("wikipedia")
        wiki_title = None

        if wikipedia_value:
            wiki_split = wikipedia_value.split(":", maxsplit=1)
            if len(wiki_split) == 2:
                wiki_lang, wiki_title = wiki_split
                wiki_lang = wiki_lang.lower()
                if wiki_lang != lang:
                    key = GET_TITLE_IN_LANGUAGE + "_" + wiki_title + "_" + wiki_lang + "_" + lang
                    wiki_title = WikipediaCache.cache_it(key, cls._wiki_session.get_title_in_language)(
                        title=wiki_title,
                        source_lang=wiki_lang,
                        dest_lang=lang
                    )

        if wiki_title:
            key = GET_SUMMARY + "_" + wiki_title + "_" + lang
            wiki_summary = WikipediaCache.cache_it(key, cls._wiki_session.get_summary)(wiki_title, lang=lang)
            if wiki_summary:
                return cls(
                    url=wiki_summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    title=wiki_summary.get("displaytitle", ""),
                    description=SizeLimiter.limit_size(wiki_summary.get("extract", "")),
                )
