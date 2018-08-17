import logging
import requests
from apistar import validators
from .base import BaseBlock, BlocksValidator
from requests.exceptions import HTTPError, RequestException, Timeout
import pybreaker
from redis import ConnectionPool, ConnectionError as RedisConnectionError, TimeoutError
from elasticsearch import Elasticsearch, ConnectionError

from redis_rate_limit import RateLimiter, TooManyRequests

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
                ip, port = redis_url.split(":")

                max_calls = int(settings['WIKI_API_RL_MAX_CALLS'])
                redis_period = int(settings['WIKI_API_RL_PERIOD'])
                redis_db = settings['WIKI_API_REDIS_DB']
                redis_timeout = int(settings['WIKI_REDIS_TIMEOUT'])

                cls._limiter = RateLimiter(
                    resource='WikipediaAPI',
                    max_requests=max_calls,
                    expire=redis_period,
                    redis_pool=ConnectionPool(host=ip, port=port, db=redis_db, socket_timeout=redis_timeout)
                )
            else:
                logging.info("No Redis URL has been provided: rate limiter not started", exc_info=True)
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
                with limiter.limit(client="Idunn"):
                    return f(*args, **kwargs)
            """
            No redis service has been set, so we
            bypass the "redis-based" rate limiter
            """
            return f(*args, **kwargs)
        return wrapper

class WikipediaBreaker:
    _breaker = None

    @classmethod
    def init_breaker(cls):
        from app import settings
        cls._breaker = pybreaker.CircuitBreaker(
                fail_max = settings['WIKI_API_CIRCUIT_MAXFAIL'],
                reset_timeout = settings['WIKI_API_CIRCUIT_TIMEOUT'],
                exclude = [HTTPError40X]
        )

    @classmethod
    def get_breaker(cls):
        if cls._breaker is None:
            cls.init_breaker()
        return cls._breaker

    @classmethod
    def handle_requests_error(cls, f):
        def wrapper(*args, **kwargs):

            breaker = cls.get_breaker()

            try:
                return WikipediaLimiter.request(breaker(f))(*args, **kwargs)
            except pybreaker.CircuitBreakerError:
                logging.info("Got CircuitBreakerError in {}".format(f.__name__), exc_info=True)
            except HTTPError:
                logging.info("Got HTTP error in {}".format(f.__name__), exc_info=True)
            except Timeout:
                logging.warning("External API timed out in {}".format(f.__name__), exc_info=True)
            except RequestException:
                logging.error("Got Request exception in {}".format(f.__name__), exc_info=True)
            except TooManyRequests:
                logging.info("Got TooManyRequests{}".format(f.__name__), exc_info=True)
            except RedisConnectionError:
                logging.info("Got redis ConnectionError{}".format(f.__name__), exc_info=True)
            except TimeoutError:
                logging.info("Got redis TimeoutError{}".format(f.__name__), exc_info=True)

        return wrapper

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
        resp = self.session.get(url=url, params={"redirect": True}, timeout=self.timeout)
        if 400 <= resp.status_code < 500:
            raise HTTPError40X
        resp.raise_for_status()
        return resp.json()

    @WikipediaBreaker.handle_requests_error
    def get_title_in_language(self, title, source_lang, dest_lang):
        url = self.API_PHP_BASE_PATTERN.format(lang=source_lang)
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
                logging.warning(
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
            logging.warning("Wiki ES not available: connection exception raised", exc_info=True)
            return None

        if len(resp) == 0:
            return None

        wiki = resp[0]['_source']

        return wiki

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
                    wiki_poi_info = WikidataConnector.get_wiki_info(wikidata_id, lang, wiki_index)
                    if wiki_poi_info is not None:
                        return cls(
                            url=wiki_poi_info.get("url"),
                            title=wiki_poi_info.get("title")[0],
                            description=wiki_poi_info.get("content"),
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
                    logging.info("WIKI_ES variable has not been set: call to Wikipedia")

        wikipedia_value = es_poi.get("properties", {}).get("wikipedia")
        wiki_title = None

        if wikipedia_value:
            wiki_split = wikipedia_value.split(":", maxsplit=1)
            if len(wiki_split) == 2:
                wiki_lang, wiki_title = wiki_split
                wiki_lang = wiki_lang.lower()
                if wiki_lang != lang:
                    wiki_title = cls._wiki_session.get_title_in_language(
                        title=wiki_title, source_lang=wiki_lang, dest_lang=lang
                    )

        if wiki_title:
            wiki_summary = cls._wiki_session.get_summary(wiki_title, lang=lang)
            if wiki_summary:
                return cls(
                    url=wiki_summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    title=wiki_summary.get("displaytitle", ""),
                    description=wiki_summary.get("extract", ""),
                )
