from enum import Enum
from fastapi import HTTPException
from elasticsearch import (
    Elasticsearch,
    ConnectionError,
    NotFoundError,
    ElasticsearchException,
)
import logging
from idunn import settings
from idunn.blocks import (
    Weather,
    AirQuality,
    ContactBlock,
    DescriptionEvent,
    GradesBlock,
    HappyHourBlock,
    ImagesBlock,
    InformationBlock,
    OpeningDayEvent,
    OpeningHourBlock,
    Covid19Block,
    PhoneBlock,
    RecyclingBlock,
    WebSiteBlock,
    WikiUndefinedException,
)
from idunn.utils import prometheus
from idunn.utils.index_names import INDICES
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.places.exceptions import PlaceNotFound

logger = logging.getLogger(__name__)


class Verbosity(str, Enum):
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
        HappyHourBlock,
        PhoneBlock,
        InformationBlock,
        WebSiteBlock,
        ContactBlock,
        ImagesBlock,
        GradesBlock,
        RecyclingBlock,
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
    ],
    Verbosity.SHORT: [OpeningHourBlock, Covid19Block],
}

PLACE_DEFAULT_INDEX = settings["PLACE_DEFAULT_INDEX"]
PLACE_POI_INDEX = settings["PLACE_POI_INDEX"]
PLACE_ADDRESS_INDEX = settings["PLACE_ADDRESS_INDEX"]
PLACE_STREET_INDEX = settings["PLACE_STREET_INDEX"]

ANY = "*"


class WikidataConnector:
    _wiki_es = None
    _es_lang = None

    @classmethod
    def get_wiki_index(cls, lang):
        if cls._es_lang is None:
            cls._es_lang = settings["ES_WIKI_LANG"].split(",")
        if lang in cls._es_lang:
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
            else:
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
        except ElasticsearchException as e:
            logger.warning("Wiki ES failure: unknown elastic error", exc_info=True)
            return None

        if len(resp) == 0:
            return None

        wiki = resp[0]["_source"]
        return wiki


def fetch_es_poi(id, es) -> dict:
    """Returns the raw POI data
    @deprecated by fetch_es_place()

    This function gets from Elasticsearch the
    entry corresponding to the given id.
    """
    try:
        return fetch_es_place(id, es, type="poi")["_source"]
    except PlaceNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)


def fetch_es_pois(raw_filters, bbox, max_size) -> list:
    es = get_elasticsearch()
    left, bot, right, top = bbox[0], bbox[1], bbox[2], bbox[3]

    terms_filters = []
    for pair in raw_filters:
        (cls, subcls) = pair.split(",", 1)
        if (cls, subcls) == (ANY, ANY):
            terms_filters.append([])
        elif subcls == ANY:
            terms_filters.append(["class_" + cls])
            terms_filters.append([cls])
        elif cls == ANY:
            terms_filters.append(["subclass_" + subcls])
        else:
            terms_filters.append(["class_" + cls, "subclass_" + subcls])

    should_terms = []
    for filt in terms_filters:
        if filt == []:
            should_terms.append({"match_all": {}})
        else:
            should_terms.append(
                {"bool": {"must": [{"term": {"poi_type.name": term}} for term in filt]}}
            )

    bbox_places = es.search(
        index=INDICES["poi"],
        body={
            "query": {
                "bool": {
                    "should": should_terms,
                    "minimum_should_match": 1,
                    "filter": {
                        "geo_bounding_box": {
                            "coord": {
                                "top_left": {"lat": top, "lon": left},
                                "bottom_right": {"lat": bot, "lon": right},
                            }
                        }
                    },
                }
            },
            "sort": {"weight": "desc"},
        },
        size=max_size,
        timeout="3s",
        ignore_unavailable=True,
    )

    bbox_places = bbox_places.get("hits", {}).get("hits", [])
    return bbox_places


def fetch_es_place(id, es, type) -> dict:
    """Returns the raw Place data

    This function gets from Elasticsearch the
    entry corresponding to the given id.
    """
    if type is None:
        index_name = PLACE_DEFAULT_INDEX
    elif type not in INDICES:
        raise HTTPException(status_code=400, detail=f"Wrong type parameter: type={type}")
    else:
        index_name = INDICES.get(type)

    try:
        es_places = es.search(
            index=index_name,
            body={"query": {"bool": {"filter": {"term": {"_id": id}}}}},
            ignore_unavailable=True,
            _source_exclude=["boundary"],
        )
    except ElasticsearchException as error:
        logger.warning(f"error with database: {error}")
        raise HTTPException(detail="database issue", status_code=503)

    es_place = es_places.get("hits", {}).get("hits", [])
    if len(es_place) == 0:
        if type is None:
            message = f"place '{id}' not found"
        else:
            message = f"place '{id}' not found with type={type}"
        raise PlaceNotFound(message=message)
    if len(es_place) > 1:
        logger.warning("Got multiple places with id %s", id)

    return es_place[0]


def fetch_closest(lat, lon, max_distance, es):
    es_addrs = es.search(
        index=",".join([PLACE_ADDRESS_INDEX, PLACE_STREET_INDEX]),
        body={
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "filter": {
                                "geo_distance": {
                                    "distance": "{}m".format(max_distance),
                                    "coord": {"lat": lat, "lon": lon},
                                    "distance_type": "plane",
                                }
                            }
                        }
                    },
                    "boost_mode": "replace",
                    "functions": [
                        {
                            "gauss": {
                                "coord": {
                                    "origin": {"lat": lat, "lon": lon},
                                    "scale": "{}m".format(max_distance),
                                }
                            }
                        }
                    ],
                }
            },
            "from": 0,
            "size": 1,
        },
    )
    es_addrs = es_addrs.get("hits", {}).get("hits", [])
    if len(es_addrs) == 0:
        raise HTTPException(
            status_code=404, detail=f"nothing around {lat}:{lon} within {max_distance}m..."
        )
    return es_addrs[0]


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


def get_geom(es_place):
    """Return the correct geometry from the elastic response

    A correct geometry means both lat and lon coordinates are required
    >>> from idunn.places import POI
    >>> get_geom(POI({})) is None
    True

    >>> get_geom(POI({'coord':{"lon": None, "lat": 48.858260156496016}})) is None
    True

    >>> get_geom(POI({'coord':{"lon": 2.2944990157640612, "lat": None}})) is None
    True

    >>> get_geom(POI({'coord':{"lon": 2.2944990157640612, "lat": 48.858260156496016}}))
    {'type': 'Point', 'coordinates': [2.2944990157640612, 48.858260156496016], 'center': [2.2944990157640612, 48.858260156496016]}
    """
    geom = None
    coord = es_place.get_coord()
    if coord is not None:
        lon = coord.get("lon")
        lat = coord.get("lat")
        if lon is not None and lat is not None:
            geom = {"type": "Point", "coordinates": [lon, lat], "center": [lon, lat]}
            if "bbox" in es_place:
                geom["bbox"] = es_place.get("bbox")
    return geom


def get_name(properties, lang):
    """Return the Place name from the properties field of the elastic response
    Here 'name' corresponds to the POI name in the language of the user request (i.e. 'name:{lang}' field).

    If lang is None or if name:lang is not in the properties
    Then name receives the local name value

    'local_name' corresponds to the name in the language of the country where the POI is located.

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
