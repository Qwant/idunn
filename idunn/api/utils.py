from enum import Enum
from elasticsearch import (
    Elasticsearch,
    ConnectionError,
    NotFoundError,
    ElasticsearchException,
)
import os
import logging
from idunn import settings
from idunn.blocks import (
    Weather,
    AirQuality,
    ContactBlock,
    DescriptionEvent,
    GradesBlock,
    ImagesBlock,
    InformationBlock,
    OpeningDayEvent,
    OpeningHourBlock,
    Covid19Block,
    PhoneBlock,
    RecyclingBlock,
    WebSiteBlock,
    WikiUndefinedException,
    TransactionalBlock,
    SocialBlock,
)
from idunn.utils import prometheus
from idunn.utils.settings import _load_yaml_file
from idunn.datasources.mimirsbrunn import MimirPoiFilter

logger = logging.getLogger(__name__)


class Type(str, Enum):
    # pylint: disable=invalid-name
    # City = "city" # this field is available in Bragi but deprecated
    House = "house"
    Poi = "poi"
    StopArea = "public_transport:stop_area"
    Street = "street"
    Zone = "zone"


def get_categories():
    categories_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml"
    )
    return _load_yaml_file(categories_path)["categories"]


def get_outing_types():
    outing_types_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml"
    )
    return _load_yaml_file(outing_types_path)["outing_types"]


ALL_CATEGORIES = get_categories()
ALL_OUTING_CATEGORIES = get_outing_types()


class CategoryEnum(str):
    """
    Methods defining the behavior of the enum `Category` defined bellow.
    """

    def match_brand(self):
        return ALL_CATEGORIES[self].get("match_brand", False)

    def pj_filters(self):
        return ALL_CATEGORIES[self].get("pj_filters")

    def pj_what(self):
        return ALL_CATEGORIES[self].get("pj_what")

    def raw_filters(self) -> [MimirPoiFilter]:
        raw_filters = ALL_CATEGORIES[self].get("raw_filters")
        filters = []
        for f in raw_filters:
            f = f.copy()
            poi_class = f.pop("class", None)
            poi_subclass = f.pop("subclass", None)
            filters.append(MimirPoiFilter(poi_class, poi_subclass, extra=f))
        return filters

    def regex(self):
        return ALL_CATEGORIES[self].get("regex")


# Load the list of categories as an enum for validation purpose
Category = Enum("Category", {cat: cat for cat in ALL_CATEGORIES}, type=CategoryEnum)


class OutingCategoryEnum(str):
    """
    Methods defining the behavior of the enum `OutingCategory` defined bellow.
    """

    def languages(self):
        return ALL_OUTING_CATEGORIES[self]


# Load the list of outing categories as an enum for validation purpose
OutingCategory = Enum(
    "OutingCategory", {cat: cat for cat in ALL_OUTING_CATEGORIES}, type=OutingCategoryEnum
)


class Verbosity(str, Enum):
    """
    Control the verbosity of the output.
    """

    LONG = "long"
    SHORT = "short"
    LIST = "list"

    @classmethod
    def default(cls):
        return cls.LONG

    @classmethod
    def default_list(cls):
        return cls.LIST


BLOCKS_BY_VERBOSITY = {
    Verbosity.LONG: [
        AirQuality,
        Weather,
        OpeningDayEvent,
        DescriptionEvent,
        OpeningHourBlock,
        Covid19Block,
        PhoneBlock,
        InformationBlock,
        WebSiteBlock,
        ContactBlock,
        ImagesBlock,
        GradesBlock,
        RecyclingBlock,
        TransactionalBlock,
        SocialBlock,
    ],
    Verbosity.LIST: [
        OpeningDayEvent,
        DescriptionEvent,
        OpeningHourBlock,
        Covid19Block,
        PhoneBlock,
        WebSiteBlock,
        ImagesBlock,
        GradesBlock,
        RecyclingBlock,
        TransactionalBlock,
        SocialBlock,
    ],
    Verbosity.SHORT: [OpeningHourBlock, Covid19Block],
}


class WikidataConnector:
    _wiki_es = None

    @classmethod
    def get_wiki_index(cls, lang):
        if lang in settings["ES_WIKI_LANG"].split(","):
            return "wikidata_{}".format(lang)
        return None

    @classmethod
    def init_wiki_es(cls):
        if cls._wiki_es is None:
            wiki_es = settings.get("WIKI_ES")
            wiki_es_max_retries = settings.get("WIKI_ES_MAX_RETRIES")
            wiki_es_timeout = settings.get("WIKI_ES_TIMEOUT")

            if wiki_es is None:
                raise WikiUndefinedException

            cls._wiki_es = Elasticsearch(
                wiki_es, max_retries=wiki_es_max_retries, timeout=wiki_es_timeout
            )

    @classmethod
    def get_wiki_info(cls, wikidata_id, wiki_index):
        cls.init_wiki_es()
        try:
            with prometheus.wiki_request_duration("wiki_es", "get_wiki_info"):
                resp = (
                    cls._wiki_es.search(
                        index=wiki_index,
                        body={
                            "query": {"bool": {"filter": {"term": {"wikibase_item": wikidata_id}}}}
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
                wiki_index,
                exc_info=True,
            )
            return None
        except ElasticsearchException:
            logger.warning("Wiki ES failure: unknown elastic error", exc_info=True)
            return None

        if len(resp) == 0:
            return None

        wiki = resp[0]["_source"]
        return wiki


def build_blocks(es_poi, lang, verbosity):
    """Returns the list of blocks we want
    depending on the verbosity.
    """
    blocks = []
    for c in BLOCKS_BY_VERBOSITY[verbosity]:
        if not c.is_enabled():
            continue
        block = c.from_es(es_poi, lang)
        if block is not None:
            blocks.append(block)
    return blocks


def get_name(properties, lang):
    """
    Return the Place name from the properties field of the elastic response. Here 'name'
    corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

    If lang is None or if name:lang is not in the properties then name receives the local name
    value.

    >>> get_name({}, 'fr') is None
    True

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, None)
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'cz')
    'spontini'

    >>> get_name({'name':'spontini', 'name:en':'spontinien', 'name:fr':'spontinifr'}, 'fr')
    'spontinifr'
    """
    name = properties.get(f"name:{lang}")
    if name is None:
        name = properties.get("name")
    return name
