import logging
import urllib.parse
from enum import Enum
from starlette.datastructures import URL
from fastapi import HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import confloat


from idunn import settings

from idunn.utils.es_wrapper import get_elasticsearch
from idunn.utils.covid19_dataset import covid19_osm_task
from idunn.places import Place, Latlon
from idunn.places.base import BasePlace
from idunn.places.exceptions import PlaceNotFound
from idunn.places.exceptions import RedirectToPlaceId, InvalidPlaceId
from .closest import get_closest_place

from ..utils.place import place_from_id
from ..utils.verbosity import Verbosity

logger = logging.getLogger(__name__)


class PlaceType(str, Enum):
    ADDRESS = "address"
    ADMIN = "admin"
    POI = "poi"
    STREET = "street"


def validate_lang(lang):
    if not lang:
        return settings["DEFAULT_LANGUAGE"]
    return lang.lower()


def log_place_request(place: BasePlace, headers):
    custom_data = {
        "id": place.get_id(),
        "name": place.get_local_name(),
        "class_name": place.get_class_name(),
        "subclass_name": place.get_subclass_name(),
    }

    if "X-QwantMaps-FocusPosition" in headers:
        pos = headers.get("X-QwantMaps-FocusPosition", "").split(";")
        if len(pos) == 3:
            try:
                custom_data["lon"] = float(pos[0])
                custom_data["lat"] = float(pos[1])
                custom_data["zoom"] = float(pos[2])
            except ValueError:
                logger.warning(
                    'Invalid data given through "X-QwantMaps-FocusPosition" header', exc_info=True
                )
    if "X-QwantMaps-Query" in headers:
        query = headers.get("X-QwantMaps-Query", "")
        if len(query) > 0:
            custom_data["query"] = urllib.parse.unquote_plus(query)
    if "X-QwantMaps-SuggestionRank" in headers:
        ranking = headers.get("X-QwantMaps-SuggestionRank", "")
        if len(ranking) > 0:
            try:
                ranking = int(ranking)
                custom_data["ranking"] = ranking
            except ValueError:
                logger.warning(
                    'Invalid data given through "X-QwantMaps-SuggestionRank" header', exc_info=True
                )
    if "X-QwantMaps-QueryLang" in headers:
        lang = headers.get("X-QwantMaps-QueryLang", "")
        if len(lang) > 0:
            custom_data["lang"] = lang

    logger.info("Received details about user query", extra={"user_selection": custom_data})


def get_place(
    id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    lang: str = None,
    type: Optional[PlaceType] = Query(
        None, description="Restrict the type of documents to search in."
    ),
    verbosity: Verbosity = Verbosity.default(),
) -> Place:
    """Main handler that returns the requested place."""
    lang = validate_lang(lang)
    try:
        place = place_from_id(id, lang, type)
    except InvalidPlaceId as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except PlaceNotFound as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except RedirectToPlaceId as e:
        path_prefix = request.headers.get("x-forwarded-prefix", "").rstrip("/")
        path = request.app.url_path_for("get_place", id=e.target_id)
        query = request.url.query
        return JSONResponse(
            status_code=303,
            headers={"location": str(URL(path=f"{path_prefix}{path}", query=query))},
            content={"id": e.target_id},
        )
    log_place_request(place, request.headers)
    if settings["BLOCK_COVID_ENABLED"] and settings["COVID19_USE_REDIS_DATASET"]:
        background_tasks.add_task(covid19_osm_task)
    return place.load_place(lang, verbosity)


def get_place_latlon(
    lat: confloat(ge=-90, le=90),
    lon: confloat(ge=-180, le=180),
    lang: str = None,
    verbosity: Verbosity = Verbosity.default(),
) -> Place:
    """Find the closest place to a point."""

    es = get_mimir_elasticsearch()
    lang = validate_lang(lang)
    try:
        closest_place = get_closest_place(lat, lon, es)
    except HTTPException:
        closest_place = None
    place = Latlon(lat, lon, closest_address=closest_place)
    return place.load_place(lang, verbosity)
