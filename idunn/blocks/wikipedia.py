import logging
import requests
from apistar import validators
from .base import BaseBlock, BlocksValidator
from requests.exceptions import HTTPError, RequestException, Timeout
import pybreaker
from elasticsearch import Elasticsearch

class HTTPError40X(HTTPError):
    pass

class WikipediaBreaker:
    _breaker = None

    @classmethod
    def init_breaker(cls):
        from app import settings
        cls._breaker = pybreaker.CircuitBreaker(
                fail_max = settings['WIKI_API_CIRCUIT_MAXFAIL'],
                reset_timeout = settings['WIKI_API_CIRCUIT_TIMEOUT'],
                exclude = [HTTPError40X])

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
                return breaker(f)(*args, **kwargs)
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

class Wikidata:
    _wiki_es = None
    _es_lang = None

    @classmethod
    def init_lang(cls):
        from app import settings
        cls._es_lang = settings['ES_WIKI_LANG'].split(',')

    @classmethod
    def get_wiki_index(cls, lang):
        if cls._es_lang is None:
            cls.init_lang()
        if lang in cls._es_lang:
            return "wikidata_{}".format(lang)
        return None

    @classmethod
    def get_wiki_es(cls):
        if cls._wiki_es is None:
            from app import settings
            cls._wiki_es = Elasticsearch(settings['WIKI_ES'])
        return cls._wiki_es

    @classmethod
    def get_wiki_info(cls, wikidata_id, lang, wiki_index):

        resp = cls.get_wiki_es().search(
            index=wiki_index,
            body={
                "filter": {
                    "term": {
                        "wikibase_item": wikidata_id
                    }
                }
            }
        ).get('hits', {}).get('hits', [])

        if len(resp) == 0:
            return None

        wiki = resp[0]['_source']
        return (wiki.get("url"), wiki.get("title"), wiki.get("content"))

class WikipediaBlock(BaseBlock):
    BLOCK_TYPE = "wikipedia"

    url = validators.String()
    title = validators.String()
    description = validators.String()

    _wiki_session = WikipediaSession()

    @classmethod
    def from_es(cls, es_poi, lang):
        """
        If wikidata id is present, then we fetch our WIKI_ES,
        else if the request lang is not in the lang white list,
        then we fetch the wikipedia API.
        """
        wikidata_id = es_poi.get("properties", {}).get("wikidata")
        if wikidata_id is not None:
            wiki_index = Wikidata.get_wiki_index(lang)
            if wiki_index is not None:
                wiki_poi_info = Wikidata.get_wiki_info(wikidata_id, lang, wiki_index)
                if wiki_poi_info is not None:
                    return cls(
                        url=wiki_poi_info[0],
                        title=wiki_poi_info[1][0],
                        description=wiki_poi_info[2],
                    )
                else:
                    return None

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
