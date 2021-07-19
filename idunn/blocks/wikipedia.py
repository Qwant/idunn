import logging
import requests
import pybreaker
from requests.exceptions import HTTPError, RequestException, Timeout
from redis import RedisError
from typing import ClassVar, Literal

from idunn import settings
from idunn.datasources.wiki_es import wiki_es
from idunn.utils import prometheus
from idunn.utils.redis import RedisWrapper
from idunn.utils.circuit_breaker import IdunnCircuitBreaker
from idunn.utils.rate_limiter import IdunnRateLimiter, TooManyRequestsException
from .base import BaseBlock


GET_WIKI_INFO = "get_wiki_info"
GET_TITLE_IN_LANGUAGE = "get_title_in_language"
GET_SUMMARY = "get_summary"

logger = logging.getLogger(__name__)


class WikipediaSession:
    _session = None
    _rate_limiter = None
    timeout = 1.0  # seconds

    API_V1_BASE_PATTERN = "https://{lang}.wikipedia.org/api/rest_v1"
    API_PHP_BASE_PATTERN = "https://{lang}.wikipedia.org/w/api.php"

    circuit_breaker = IdunnCircuitBreaker(
        "wikipedia_api_breaker",
        int(settings["WIKI_BREAKER_MAXFAIL"]),
        int(settings["WIKI_BREAKER_TIMEOUT"]),
    )

    class Helpers:
        @staticmethod
        def handle_requests_error(f):
            def wrapped_f(*args, **kwargs):
                try:
                    with WikipediaSession.get_rate_limiter().limit(client="idunn"):
                        return f(*args, **kwargs)
                except pybreaker.CircuitBreakerError:
                    prometheus.exception("CircuitBreakerError")
                    logger.error(
                        "Got CircuitBreakerError in %s",
                        f.__name__,
                        exc_info=True,
                    )
                except HTTPError:
                    prometheus.exception("HTTPError")
                    logger.warning("Got HTTP error in %s", f.__name__, exc_info=True)
                except Timeout:
                    prometheus.exception("RequestsTimeout")
                    logger.warning("External API timed out in %s", f.__name__, exc_info=True)
                except RequestException:
                    prometheus.exception("RequestException")
                    logger.error("Got Request exception in %s", f.__name__, exc_info=True)
                except TooManyRequestsException:
                    prometheus.exception("TooManyRequests")
                    logger.warning("Got TooManyRequests in %s", f.__name__, exc_info=True)
                except RedisError:
                    prometheus.exception("RedisError")
                    logger.warning("Got redis ConnectionError in %s", f.__name__, exc_info=True)
                return None

            return wrapped_f

    @property
    def session(self):
        if self._session is None:
            user_agent = settings["WIKI_USER_AGENT"]
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": user_agent})
        return self._session

    @classmethod
    def get_rate_limiter(cls):
        if cls._rate_limiter is None:
            cls._rate_limiter = IdunnRateLimiter(
                resource="WikipediaAPI",
                max_requests=int(settings["WIKI_API_RL_MAX_CALLS"]),
                expire=int(settings["WIKI_API_RL_PERIOD"]),
            )
        return cls._rate_limiter

    @Helpers.handle_requests_error
    @circuit_breaker
    def get_summary(self, title, lang):
        url = "{base_url}/page/summary/{title}".format(
            base_url=self.API_V1_BASE_PATTERN.format(lang=lang), title=title
        )

        with prometheus.wiki_request_duration("wiki_api", "get_summary"):
            resp = self.session.get(url=url, params={"redirect": True}, timeout=self.timeout)

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
                logger.warning("Got multiple pages in wikipedia langlinks response: %s", resp_data)
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
        max_wiki_desc_size = settings["WIKI_DESC_MAX_SIZE"]
        return (
            (content[:max_wiki_desc_size] + "...") if len(content) > max_wiki_desc_size else content
        )


class WikipediaBlock(BaseBlock):
    type: Literal["wikipedia"] = "wikipedia"
    url: str
    title: str
    description: str

    _wiki_session: ClassVar = WikipediaSession()

    @classmethod
    def from_es(cls, place, lang):
        # If `wikidata_id` is present and `lang` is available in `wiki_es`, try
        # to fetch from ES, otherwise we fetch the wikipedia API.
        if place.wikidata_id is not None and wiki_es.enabled() and wiki_es.is_lang_available(lang):
            wiki_poi_info = wiki_es.get_info(place.wikidata_id, lang)

            if wiki_poi_info is None:
                return None

            return cls(
                url=wiki_poi_info.get("url"),
                title=wiki_poi_info.get("title")[0],
                description=SizeLimiter.limit_size(wiki_poi_info.get("content", "")),
            )

        wikipedia_value = place.properties.get("wikipedia")
        wiki_title = None

        if wikipedia_value:
            wiki_split = wikipedia_value.split(":", maxsplit=1)
            if len(wiki_split) == 2:
                wiki_lang, wiki_title = wiki_split
                wiki_lang = wiki_lang.lower()
                if wiki_lang != lang:
                    key = GET_TITLE_IN_LANGUAGE + "_" + wiki_title + "_" + wiki_lang + "_" + lang
                    wiki_title = RedisWrapper.cache_it(
                        key, cls._wiki_session.get_title_in_language
                    )(title=wiki_title, source_lang=wiki_lang, dest_lang=lang)

        if wiki_title:
            key = GET_SUMMARY + "_" + wiki_title + "_" + lang
            wiki_summary = RedisWrapper.cache_it(key, cls._wiki_session.get_summary)(
                wiki_title, lang=lang
            )
            if wiki_summary:
                return cls(
                    url=wiki_summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    title=wiki_summary.get("displaytitle", ""),
                    description=SizeLimiter.limit_size(wiki_summary.get("extract", "")),
                )

        return None
