import logging
import requests
import pybreaker
from requests.exceptions import HTTPError, RequestException, Timeout
from redis import RedisError

from idunn import settings
from idunn.utils import prometheus
from idunn.utils.redis import RedisWrapper
from idunn.utils.circuit_breaker import IdunnCircuitBreaker
from idunn.utils.rate_limiter import IdunnRateLimiter, TooManyRequestsException


logger = logging.getLogger(__name__)


class WikipediaSession:
    TIMEOUT = 1.0  # seconds

    API_V1_BASE_PATTERN = "https://{lang}.wikipedia.org/api/rest_v1"
    API_PHP_BASE_PATTERN = "https://{lang}.wikipedia.org/w/api.php"

    REDIS_GET_SUMMARY_PREFIX = "get_summary"
    REDIS_TITLE_IN_LANG_PREFIX = "get_title_in_language"

    circuit_breaker = IdunnCircuitBreaker(
        "wikipedia_api_breaker",
        int(settings["WIKI_BREAKER_MAXFAIL"]),
        int(settings["WIKI_BREAKER_TIMEOUT"]),
    )

    class Helpers:
        _rate_limiter = None

        @classmethod
        def get_rate_limiter(cls):
            if cls._rate_limiter is None:
                cls._rate_limiter = IdunnRateLimiter(
                    resource="WikipediaAPI",
                    max_requests=int(settings["WIKI_API_RL_MAX_CALLS"]),
                    expire=int(settings["WIKI_API_RL_PERIOD"]),
                )

            return cls._rate_limiter

        @classmethod
        def handle_requests_error(cls, f):
            """
            Helper function to catch exceptions and log them into Prometheus.
            """

            def wrapped_f(*args, **kwargs):
                try:
                    with cls.get_rate_limiter().limit(client="idunn"):
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

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings["WIKI_USER_AGENT"]})

    def get_summary(self, title, lang):
        @self.Helpers.handle_requests_error
        @self.circuit_breaker
        def fetch_data():
            url = "{base_url}/page/summary/{title}".format(
                base_url=self.API_V1_BASE_PATTERN.format(lang=lang),
                title=title,
            )

            with prometheus.wiki_request_duration("wiki_api", "get_summary"):
                resp = self.session.get(url=url, params={"redirect": True}, timeout=self.TIMEOUT)

            resp.raise_for_status()
            return resp.json()

        key = self.REDIS_GET_SUMMARY_PREFIX + "_" + title + "_" + lang
        fetch_data_cached = RedisWrapper.cache_it(key, fetch_data)
        return fetch_data_cached()

    def get_title_in_language(self, title, source_lang, dest_lang):
        @self.Helpers.handle_requests_error
        @self.circuit_breaker
        def fetch_data():
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
                    timeout=self.TIMEOUT,
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

        key = self.REDIS_TITLE_IN_LANG_PREFIX + "_" + title + "_" + source_lang + "_" + dest_lang
        fetch_data_cached = RedisWrapper.cache_it(key, fetch_data)
        return fetch_data_cached()


wikipedia_session = WikipediaSession()
