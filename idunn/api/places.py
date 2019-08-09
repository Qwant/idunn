import json
import logging
import urllib.parse
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest, NotFound
from apistar.http import Response, Headers

from idunn import settings
from idunn.utils import prometheus
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI, Latlon
from idunn.api.utils import fetch_es_place, DEFAULT_VERBOSITY, ALL_VERBOSITY_LEVELS
from idunn.api.pages_jaunes import pj_source
from .closest import get_closest_place


logger = logging.getLogger(__name__)


def validate_verbosity(verbosity):
    if verbosity not in ALL_VERBOSITY_LEVELS:
        raise BadRequest({
            "message": f"Unknown verbosity '{verbosity}'. Accepted values are {ALL_VERBOSITY_LEVELS}"
        })
    return verbosity


def validate_lang(lang):
    if not lang:
        return settings['DEFAULT_LANGUAGE']
    return lang.lower()


def log_custom_headers(id, headers: Headers):
    custom_data = {}
    if 'X-QwantMaps-FocusPosition' in headers:
        pos = headers.get('X-QwantMaps-FocusPosition', '').split(';')
        if len(pos) == 3:
            try:
                lon = float(pos[0])
                lat = float(pos[1])
                zoom = float(pos[2])
                custom_data['lon'] = lon
                custom_data['lat'] = lat
                custom_data['zoom'] = zoom
            except Exception:
                logger.warning('Invalid data given through "X-QwantMaps-FocusPosition" header', exc_info=True)
    if 'X-QwantMaps-Query' in headers:
        query = headers.get('X-QwantMaps-Query', '')
        if len(query) > 0:
            custom_data['query'] = urllib.parse.unquote_plus(query)
    if 'X-QwantMaps-SuggestionRank' in headers:
        ranking = headers.get('X-QwantMaps-SuggestionRank', '')
        if len(ranking) > 0:
            try:
                ranking = int(ranking)
                custom_data['ranking'] = ranking
            except Exception:
                logger.warning('Invalid data given through "X-QwantMaps-SuggestionRank" header', exc_info=True)
    if 'X-QwantMaps-QueryLang' in headers:
        lang = headers.get('X-QwantMaps-QueryLang', '')
        if len(lang) > 0:
            custom_data['lang'] = lang
    if len(custom_data) > 0:
        custom_data['id'] = id
        logger.info('Received details about user query', extra={'user_selection': custom_data})


def get_place(id, es: Elasticsearch, indices: IndexNames, headers: Headers, lang=None, type=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    log_custom_headers(id, headers)

    """Main handler that returns the requested place"""
    verbosity = validate_verbosity(verbosity)
    lang = validate_lang(lang)

    if id.startswith(pj_source.PLACE_ID_PREFIX):
        pj_place = pj_source.get_place(id)
        return pj_place.load_place(lang, verbosity)

    es_place = fetch_es_place(id, es, indices, type)

    places = {
        "admin": Admin,
        "street": Street,
        "addr": Address,
        "poi": POI,
    }
    loader = places.get(es_place.get('_type'))

    if loader is None:
        prometheus.exception("FoundPlaceWithWrongType")
        raise Exception("Place with id '{}' has a wrong type: '{}'".format(id, es_place[0].get('_type')))

    return loader(es_place['_source']).load_place(lang, verbosity)


def get_place_latlon(lat: float, lon: float, es: Elasticsearch, lang=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    verbosity = validate_verbosity(verbosity)
    lang = validate_lang(lang)
    try:
        closest_place = get_closest_place(lat, lon, es)
    except NotFound:
        closest_place = None
    place = Latlon(lat, lon, closest_address=closest_place)
    return place.load_place(lang, verbosity)


def handle_option(id, headers: Headers):
    if settings.get('CORS_OPTIONS_REQUESTS_ENABLED', False) is True:
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': headers.get('Access-Control-Request-Headers', '*'),
            'Access-Control-Allow-Methods': 'GET',
        }
        return Response('', headers=headers)
    return Response('', status_code=405)
