import json
import logging
import requests
import pybreaker

from apistar import validators
from .base import BaseBlock, BlocksValidator
from requests.exceptions import HTTPError, RequestException, Timeout
from redis import Redis, ConnectionPool, ConnectionError as RedisConnectionError, TimeoutError, RedisError
from elasticsearch import Elasticsearch, ConnectionError
from redis_rate_limit import RateLimiter, TooManyRequests
from idunn.utils import prometheus

GET_WIKI_INFO = "get_wiki_info"
GET_TITLE_IN_LANGUAGE = "get_title_in_language"
GET_SUMMARY = "get_summary"

logger = logging.getLogger(__name__)

class HTTPError40X(HTTPError):
    pass

class WikipediaLimiter:
    _limiter = None

    @classmethod
    def get_limiter(cls):
        if cls._limiter is None:
            from app import settings

            redis_url = settings['WIKI_API_REDIS_URL']

            if redis_url is not None:
                """
                If a redis url has been provided to Idunn,
                then we use the corresponding redis
                service in the rate limiter.
                """
                max_calls = int(settings['WIKI_API_RL_MAX_CALLS'])
                redis_period = int(settings['WIKI_API_RL_PERIOD'])

                redis_url = "redis://" + redis_url
                redis_db = settings['WIKI_API_REDIS_DB']
                redis_timeout = int(settings['WIKI_REDIS_TIMEOUT'])

                try:
                    pool = ConnectionPool.from_url(redis_url, db=redis_db, socket_timeout=redis_timeout)
                except RedisError:
                    logger.warning("No Redis instance available for limiter", exc_info=True)
                    cls._limiter = False

                cls._limiter = RateLimiter(
                    resource='WikipediaAPI',
                    max_requests=max_calls,
                    expire=redis_period,
                    redis_pool=pool
                )
            else:
                logger.warning("No Redis URL has been provided: rate limiter not started", exc_info=True)
                cls._limiter = False
        return cls._limiter

    @classmethod
    def request(cls, f):
        def wrapper(*args, **kwargs):
            limiter = cls.get_limiter()

            if limiter is not False:
                """
                We use the RateLimiter since
                the redis service url has been provided
                """
                try:
                    with limiter.limit(client="Idunn"):
                        return f(*args, **kwargs)
                except RedisError:
                    logger.error("Got a RedisError in {}".format(f.__name__), exc_info=True)
                    return None
            """
            No redis service has been set, so we
            bypass the "redis-based" rate limiter
            """
            return f(*args, **kwargs)
        return wrapper

class LogListener(pybreaker.CircuitBreakerListener):

    def state_change(self, cb, old_state, new_state):
        msg = "State Change: CB: {0}, From: {1} to New State: {2}".format(cb.name, old_state, new_state)
        logger.warning(msg)

class WikipediaBreaker:
    _breaker = None

    @classmethod
    def init_breaker(cls):
        from app import settings
        cls._breaker = pybreaker.CircuitBreaker(
                fail_max = settings['WIKI_API_CIRCUIT_MAXFAIL'],
                reset_timeout = settings['WIKI_API_CIRCUIT_TIMEOUT'],
                exclude = [HTTPError40X],
                listeners=[LogListener()]
        )

    @classmethod
    def get_breaker(cls):
        if cls._breaker is None:
            cls.init_breaker()
        return cls._breaker

    @classmethod
    def handle_requests_error(cls, f):
        def wrapped_f(*args, **kwargs):
            breaker = cls.get_breaker()
            try:
                return WikipediaLimiter.request(breaker(f))(*args, **kwargs)
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
            except TooManyRequests:
                prometheus.exception("TooManyRequests")
                logger.warning("Got TooManyRequests{}".format(f.__name__), exc_info=True)
            except RedisConnectionError:
                prometheus.exception("RedisConnectionError")
                logger.warning("Got redis ConnectionError{}".format(f.__name__), exc_info=True)
            except TimeoutError:
                prometheus.exception("RedisTimeoutError")
                logger.warning("Got redis TimeoutError{}".format(f.__name__), exc_info=True)
        return wrapped_f

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
        except RedisError:
            prometheus.exception("RedisError")
            logging.exception("Got a RedisError")
            return None

    @classmethod
    def init_cache(cls):
        from app import settings

        redis_url = settings['WIKI_API_REDIS_URL']

        if redis_url is not None:
            cls._expire = int(settings['WIKI_CACHE_TIMEOUT']) # seconds
            redis_db = settings['WIKI_CACHE_REDIS_DB']
            redis_timeout = int(settings['WIKI_REDIS_TIMEOUT'])
            redis_url = "redis://" + redis_url

            try:
                pool = ConnectionPool.from_url(redis_url, db=redis_db, socket_timeout=redis_timeout)
            except RedisError:
                logger.warning("No Redis instance available for caching", exc_info=True)
                cls._connection = False

            cls._connection = Redis(
                connection_pool=pool
            )
        else:
            logger.warning("No Redis URL has been set for caching", exc_info=True)
            cls._connection = False

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
            if cls._connection is not False:
                value_stored = cls.get_value(key)
                if value_stored is not None:
                    return json.loads(value_stored.decode('utf-8'))
                result = f(*args, **kwargs)
                json_result = json.dumps(result)
                cls.set_value(key, json_result)
                return result
            return f(*args, **kwargs)
        return with_cache


class WikipediaSession:
    _session = None
    timeout = 1. # seconds

    API_V1_BASE_PATTERN = "https://{lang}.wikipedia.org/api/rest_v1"
    API_PHP_BASE_PATTERN = "https://{lang}.wikipedia.org/w/api.php"

    @property
    def session(self):
        if self._session is None:
            from app import settings
            user_agent = settings['WIKI_USER_AGENT']
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": user_agent})
        return self._session

    @WikipediaBreaker.handle_requests_error
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

        if 400 <= resp.status_code < 500:
            raise HTTPError40X
        resp.raise_for_status()
        return resp.json()

    @WikipediaBreaker.handle_requests_error
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

        if 400 <= resp.status_code < 500:
            raise HTTPError40X
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


class WikiUndefinedException(Exception):
    pass


class WikidataConnector:
    _wiki_es = None
    _es_lang = None

    @classmethod
    def get_wiki_index(cls, lang):
        if cls._es_lang is None:
            from app import settings
            cls._es_lang = settings['ES_WIKI_LANG'].split(',')
        if lang in cls._es_lang:
            return "wikidata_{}".format(lang)
        return None

    @classmethod
    def init_wiki_es(cls):
        if cls._wiki_es is None:
            from app import settings

            wiki_es = settings.get('WIKI_ES')
            wiki_es_max_retries = settings.get('WIKI_ES_MAX_RETRIES')
            wiki_es_timeout = settings.get('WIKI_ES_TIMEOUT')

            if wiki_es is None:
                raise WikiUndefinedException
            else:
                cls._wiki_es = Elasticsearch(
                        wiki_es,
                        max_retries=wiki_es_max_retries,
                        timeout=wiki_es_timeout
                )

    @classmethod
    def get_wiki_info(cls, wikidata_id, lang, wiki_index):
        cls.init_wiki_es()

        try:
            with prometheus.wiki_request_duration("wiki_es", "get_wiki_info"):
                resp = cls._wiki_es.search(
                    index=wiki_index,
                    body={
                        "filter": {
                            "term": {
                                "wikibase_item": wikidata_id
                            }
                        }
                    }
                ).get('hits', {}).get('hits', [])
        except ConnectionError:
            logger.warning("Wiki ES not available: connection exception raised", exc_info=True)
            return None

        if len(resp) == 0:
            return None

        wiki = resp[0]['_source']

        return wiki

class SizeLimiter:
    _max_wiki_desc_size = None

    @classmethod
    def init_max_size(cls):
        if cls._max_wiki_desc_size is None:
            from app import settings
            cls._max_wiki_desc_size = settings.get('WIKI_DESC_MAX_SIZE')

    @classmethod
    def limit_size(cls, content):
        """
        Just cut a string if its length > max_size
        """
        cls.init_max_size()
        return (content[:cls._max_wiki_desc_size] + '...') if len(content) > cls._max_wiki_desc_size else content

class WikipediaBlock(BaseBlock):
    BLOCK_TYPE = "wikipedia"

    url = validators.String()
    title = validators.String()
    description = validators.String()

    _wiki_session = WikipediaSession()

    @classmethod
    def from_es(cls, es_poi, lang):
        """
        If "wikidata_id" is present and "lang" is in "ES_WIKI_LANG",
        then we try to fetch our "WIKI_ES" (if WIKI_ES has been defined),
        else then we fetch the wikipedia API.
        """
        wikidata_id = es_poi.get("properties", {}).get("wikidata")
        if wikidata_id is not None:
            wiki_index = WikidataConnector.get_wiki_index(lang)
            if wiki_index is not None:
                try:
                    key = GET_WIKI_INFO + "_" + wikidata_id + "_" + lang + "_" + wiki_index
                    wiki_poi_info = WikipediaCache.cache_it(key, WikidataConnector.get_wiki_info)(wikidata_id, lang, wiki_index)
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

        wikipedia_value = es_poi.get("properties", {}).get("wikipedia")
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
