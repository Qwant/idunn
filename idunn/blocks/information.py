import logging
import requests
from requests.exceptions import HTTPError, RequestException, Timeout
from apistar import validators

from .base import BaseBlock, BlocksValidator


def handle_requests_error(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
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

    api_v1_base_pattern = "https://{lang}.wikipedia.org/api/rest_v1"
    api_php_base_pattern = "https://{lang}.wikipedia.org/w/api.php"

    @property
    def session(self):
        if self._session is None:
            from app import settings
            user_agent = settings['WIKI_USER_AGENT']
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": user_agent})
        return self._session

    @handle_requests_error
    def get_summary(self, title, lang):
        url = "{base_url}/page/summary/{title}".format(
            base_url=self.api_v1_base_pattern.format(lang=lang), title=title
        )
        resp = self.session.get(url=url, params={"redirect": True}, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    @handle_requests_error
    def get_title_in_language(self, title, source_lang, dest_lang):
        url = self.api_php_base_pattern.format(lang=source_lang)
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


class InformationBlock(BaseBlock):
    BLOCK_TYPE = "information"

    blocks = BlocksValidator(allowed_blocks=[WikipediaBlock])

    @classmethod
    def from_es(cls, es_poi, lang):
        blocks = []
        wikipedia_block = WikipediaBlock.from_es(es_poi, lang)
        if wikipedia_block is not None:
            blocks.append(wikipedia_block)
        if len(blocks) > 0:
            return cls(blocks=blocks)
