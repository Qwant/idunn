import logging
import urllib.parse
from starlette.datastructures import URL
from fastapi import HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse


from idunn import settings
from idunn.api.utils import Verbosity
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.utils.covid19_dataset import covid19_osm_task
from idunn.places import Place, Latlon, place_from_id
from idunn.places.base import BasePlace
from idunn.places.exceptions import PlaceNotFound
from idunn.places import Place
from idunn.places.exceptions import RedirectToPlaceId, InvalidPlaceId
from .closest import get_closest_place

logger = logging.getLogger(__name__)


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
            except Exception:
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
            except Exception:
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
    type=None,
    verbosity: Verbosity = Verbosity.default(),
) -> Place:
    """Main handler that returns the requested place"""
    lang = validate_lang(lang)
    try:
        place = place_from_id(id, type)
    except InvalidPlaceId as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PlaceNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)
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
    print(place.load_place(lang, verbosity).dict())
    return place.load_place(lang, verbosity)


def get_place_latlon(
    lat: float, lon: float, lang: str = None, verbosity: Verbosity = Verbosity.default()
) -> Place:
    es = get_elasticsearch()
    lang = validate_lang(lang)
    try:
        closest_place = get_closest_place(lat, lon, es)
    except HTTPException:
        closest_place = None
    place = Latlon(lat, lon, closest_address=closest_place)
    return place.load_place(lang, verbosity)


def handle_option(id, request: Request):
    response = Response()
    if settings.get("CORS_OPTIONS_REQUESTS_ENABLED", False) is True:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = request.headers.get(
            "Access-Control-Request-Headers", "*"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET"
    else:
        response.status_code = 405
    return response
