import logging
from elasticsearch import Elasticsearch
from apistar.exceptions import BadRequest

from idunn.utils.settings import Settings
from idunn.utils.index_names import IndexNames
from idunn.places import Place, Admin, Street, Address, POI
from idunn.api.utils import get_geom, get_name, fetch_es_venues, LONG, SHORT, DEFAULT_VERBOSITY

logger = logging.getLogger(__name__)

VERBOSITY_LEVELS = [LONG, SHORT]

def get_venues(left, bot, right, top, es: Elasticsearch, indices: IndexNames, settings: Settings, categories, lang=None, type=None, verbosity=DEFAULT_VERBOSITY):
    """
        bbox = left,bottom,right,top
    """
    if verbosity not in VERBOSITY_LEVELS:
        raise BadRequest(
            status_code=400,
            detail={"message": f"verbosity {verbosity} does not belong to the set of possible verbosity values={VERBOSITY_LEVELS}"}
        )

    if not lang:
        lang = settings['DEFAULT_LANGUAGE']
    lang = lang.lower()

    if not all([left, bot, right, top]):
        raise BadRequest(
            status_code=400,
            detail={"message": f"the bounding box is not complete"}
        )
    left, bot, right, top = float(left), float(bot), float(right), float(top)
    if left > right or bot > top:
        raise BadRequest(
            status_code=400,
            detail={"message": f"the bounding box is not valid"}
        )
    if categories is None:
        raise BadRequest(
            status_code=400,
            detail={"message": f"no categorie provided"}
        )
    categories = categories.split(",")

    es_venues = fetch_es_venues(left, bot, right, top, es, indices, categories)


    result = []
    for venue in es_venues:
        result.append(POI.load_place(venue['_source'], lang, settings, verbosity))

    return result
