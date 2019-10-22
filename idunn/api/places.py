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
from idunn.places.base import BasePlace
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


def log_place_request(place: BasePlace, headers: Headers):
    custom_data = {
        'id': place.get_id(),
        'name': place.get_local_name(),
        'class_name': place.get_class_name(),
        'subclass_name': place.get_subclass_name(),
    }

    # Filter out irrelevant fields
    for key in custom_data.keys():
        if not custom_data[key]:
            del custom_data[key]

    if 'X-QwantMaps-FocusPosition' in headers:
        pos = headers.get('X-QwantMaps-FocusPosition', '').split(';')
        if len(pos) == 3:
            try:
                custom_data['lon'] = float(pos[0])
                custom_data['lat'] = float(pos[1])
                custom_data['zoom'] = float(pos[2])
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

    logger.info(
        'Received details about user query',
        extra={'user_selection': custom_data}
    )


def get_place(id, es: Elasticsearch, indices: IndexNames, headers: Headers, lang=None, type=None, verbosity=DEFAULT_VERBOSITY) -> Place:
    """Main handler that returns the requested place"""
    verbosity = validate_verbosity(verbosity)
    lang = validate_lang(lang)

    # Handle place from "pages jaunes"
    if id.startswith(pj_source.PLACE_ID_PREFIX):
        pj_place = pj_source.get_place(id)
        log_place_request(pj_place, headers)
        return pj_place.load_place(lang, verbosity)

    # Otherwise handle places from the ES db
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

    place = loader(es_place['_source'])
    log_place_request(place, headers)
    return place.load_place(lang, verbosity)


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
