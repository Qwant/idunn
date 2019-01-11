from apistar.exceptions import NotFound, BadRequest
from idunn.blocks import PhoneBlock, OpeningHourBlock, InformationBlock, WebSiteBlock, ContactBlock, ImagesBlock, WikiUndefinedException, GET_WIKI_INFO, WikipediaCache
from elasticsearch import Elasticsearch, ConnectionError
from idunn.utils import prometheus
import logging

LONG = "long"
SHORT = "short"
DEFAULT_VERBOSITY = LONG

BLOCKS_BY_VERBOSITY = {
    LONG: [
        OpeningHourBlock,
        PhoneBlock,
        InformationBlock,
        WebSiteBlock,
        ContactBlock,
        ImagesBlock
    ],
    SHORT: [
        OpeningHourBlock
    ]
}

logger = logging.getLogger(__name__)

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
    def get_wiki_info(cls, wikidata_id, lang, wiki_index, es_poi):
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

class PlaceData(dict):
    def __init__(self, d):
        super().__init__(d)
        self._wiki_resp = None

    def get_wiki_info(self, wikidata_id, lang, wiki_index):
        return WikidataConnector.get_wiki_info(wikidata_id, lang, wiki_index, self)

    def get_wiki_index(self, lang):
        return WikidataConnector.get_wiki_index(lang)

    def get_wiki_resp(self, lang):
        if self.wiki_resp is None:
            wikidata_id = self.get("properties", {}).get("wikidata")
            if wikidata_id is not None:
                wiki_index = self.get_wiki_index(lang)
                if wiki_index is not None:
                    key = GET_WIKI_INFO + "_" + wikidata_id + "_" + lang + "_" + wiki_index
                    try:
                        self.wiki_resp = WikipediaCache.cache_it(key, WikidataConnector.get_wiki_info)(wikidata_id, lang, wiki_index, self)
                    except WikiUndefinedException:
                        logger.info("WIKI_ES variable has not been set: cannot fetch wikidata images")
                        return None
        return self.wiki_resp

    @property
    def wiki_resp(self):
        return self._wiki_resp

    @wiki_resp.setter
    def wiki_resp(self, resp):
        self._wiki_resp = resp

def fetch_es_poi(id, es) -> dict:
    """Returns the raw POI data
    @deprecated by fetch_es_place()

    This function gets from Elasticsearch the
    entry corresponding to the given id.
    """
    es_pois = es.search(index='munin_poi',
                        body={
                            "filter": {
                                "term": {"_id": id}
                            }
                        })

    es_poi = es_pois.get('hits', {}).get('hits', [])
    if len(es_poi) == 0:
        raise NotFound(detail={'message': f"poi '{id}' not found"})
    result = es_poi[0]['_source']

    # Flatten properties into result
    properties = {p.get('key'): p.get('value') for p in result.get('properties')}
    result['properties'] = properties
    return result

def fetch_es_place(id, es, indices, type) -> list:
    """Returns the raw Place data

    This function gets from Elasticsearch the
    entry corresponding to the given id.
    """
    if type is None:
        index_name = "munin"
    elif type not in indices:
        raise BadRequest(
            status_code=400,
            detail={"message": f"Wrong type parameter: type={type}"}
        )
    else:
        index_name = indices.get(type)

    es_places = es.search(index=index_name,
        body={
            "filter": {
                "term": {"_id": id}
            }
        })

    es_place = es_places.get('hits', {}).get('hits', [])
    if len(es_place) == 0:
        raise NotFound(detail={'message': f"place {id} not found with type={type}"})

    return es_place

def build_blocks(es_poi, lang, verbosity):
    """Returns the list of blocks we want
    depending on the verbosity.
    """
    blocks = []
    for c in BLOCKS_BY_VERBOSITY.get(verbosity):
        block = c.from_es(es_poi, lang)
        if block is not None:
            blocks.append(block)
    return blocks

def get_geom(es_place):
    """Return the correct geometry from the elastic response

    A correct geometry means both lat and lon coordinates are required

    >>> get_geom({}) is None
    True

    >>> get_geom({'coord':{"lon": None, "lat": 48.858260156496016}}) is None
    True

    >>> get_geom({'coord':{"lon": 2.2944990157640612, "lat": None}}) is None
    True

    >>> get_geom({'coord':{"lon": 2.2944990157640612, "lat": 48.858260156496016}})
    {'type': 'Point', 'coordinates': [2.2944990157640612, 48.858260156496016], 'center': [2.2944990157640612, 48.858260156496016]}
    """
    geom = None
    if 'coord' in es_place:
        coord = es_place.get('coord')
        lon = coord.get('lon')
        lat = coord.get('lat')
        if lon is not None and lat is not None:
            geom = {
                'type': 'Point',
                'coordinates': [lon, lat],
                'center': [lon, lat]
            }
            if 'bbox' in es_place:
                geom['bbox'] = es_place.get('bbox')
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
    name = properties.get(f'name:{lang}')
    if name is None:
        name = properties.get('name')
    return name
