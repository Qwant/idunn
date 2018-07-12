import logging
import requests
from apistar import validators
from .base import BaseBlock, BlocksValidator
from requests.exceptions import HTTPError, RequestException, Timeout
import pybreaker

class HTTPError40X(HTTPError):
    pass

class WikipediaBreaker:
    _breaker = None

    @classmethod
    def init_breaker(cls):
        from app import settings
        cls._breaker = pybreaker.CircuitBreaker(
                fail_max=settings['CIRCUIT_FAILMAX'],
                reset_timeout=settings['CIRCUIT_TIMEOUT'],
                exclude=[HTTPError40X])

    @classmethod
    def get_breaker(cls):
        if cls._breaker is None:
            cls.init_breaker()
        return cls._breaker

    @classmethod
    def handle_requests_error(cls, f):
        def wrapper(*args, **kwargs):
            if cls._breaker is None:
                cls.init_breaker()
            try:
                return cls._breaker(f)(*args, **kwargs)
            except pybreaker.CircuitBreakerError:
                logging.info("Got CircuitBreakerError in {}".format(f.__name__), exc_info=True)
            except HTTPError:
                logging.info("Got HTTP error in {}".format(f.__name__), exc_info=True)
            except Timeout:
                logging.warning("External API timed out in {}".format(f.__name__), exc_info=True)
            except RequestException:
                logging.error("Got Request exception in {}".format(f.__name__), exc_info=True)
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
        if resp.status_code in range(400, 500):
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
        if resp.status_code in range(400, 500):
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

class WikipediaBlock(BaseBlock):
    BLOCK_TYPE = "wikipedia"

    url = validators.String()
    title = validators.String()
    description = validators.String()

    _wiki_session = WikipediaSession()

    @classmethod
    def from_es(cls, es_poi, lang):
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
