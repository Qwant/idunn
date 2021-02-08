import logging
import re
from fastapi import HTTPException, Query
from fastapi.responses import ORJSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field, validator, HttpUrl
from jellyfish import damerau_levenshtein_distance
from unidecode import unidecode

from idunn import settings
from idunn.geocoder.nlu_client import nlu_client, NluClientException
from idunn.geocoder.bragi_client import bragi_client
from idunn.places import place_from_id, Place
from idunn.api.places import PlaceType
from idunn.api.places_list import get_places_bbox
from idunn.utils import maps_urls
from idunn.instant_answer import normalize
from .constants import PoiSource

logger = logging.getLogger(__name__)

nlu_allowed_languages = settings["NLU_ALLOWED_LANGUAGES"].split(",")


class InstantAnswerResult(BaseModel):
    places: List[Place] = Field(
        description="List of relevant places to display on the instant answer. "
        "At most 1 place is returned if no broad intention has been detected."
    )
    source: Optional[PoiSource] = Field(
        description=(
            "Data source for the returned place, or data provider for the list of results. This "
            "field is not provided when the instant answer relates to an admnistrative area or an "
            "address."
        )
    )
    intention_bbox: Optional[Tuple[float, float, float, float]] = Field(
        description=(
            "Bounding box where the results have been searched for, based on the detected "
            "intention. Not provided when no detected intention was used to fetch the results."
        ),
        example=(2.32, 48.85, 2.367, 48.866),
    )
    maps_url: HttpUrl = Field(description="Direct URL to the result(s) on Qwant Maps.",)
    maps_frame_url: HttpUrl = Field(
        description="URL to the map displaying the results on Qwant Maps, with no user interface. "
        "This URL can be used to display an `<iframe>`."
    )

    @validator("intention_bbox")
    def round_bbox_values(cls, v):
        if v is None:
            return v
        return tuple(round(x, 6) for x in v)


class InstantAnswerQuery(BaseModel):
    query: str
    lang: str


class InstantAnswerData(BaseModel):
    query: InstantAnswerQuery
    result: InstantAnswerResult


class InstantAnswerResponse(BaseModel):
    status: str = "success"
    data: InstantAnswerData


NoInstantAnswerToDisplay = HTTPException(status_code=404, detail="No instant answer to display")
NUM_SUFFIXES = ["bis", "ter", "quad", "e", "eme", "ème", "er", "st", "nd", "rd", "th"]


class PlaceFilter(BaseModel):
    type: PlaceType
    name: str
    postcodes: List[str] = []
    admins: List[str] = []

    @staticmethod
    def from_bragi_type(bragi_type):
        if bragi_type == "house":
            return PlaceType.ADDRESS
        if bragi_type == "poi":
            return PlaceType.POI
        if bragi_type == "street":
            return PlaceType.STREET
        if bragi_type in ("city", "zone"):
            return PlaceType.ADMIN
        raise Exception(f"unsupported type `{bragi_type}`")

    @classmethod
    def from_bragi_response(cls, bragi_response):
        if bragi_response["postcode"]:
            postcodes = bragi_response["postcode"].split(";")
        else:
            postcodes = list(
                {
                    z
                    for admin in bragi_response["administrative_regions"]
                    for z in admin["zip_codes"]
                }
            )

        return PlaceFilter(
            type=cls.from_bragi_type(bragi_response["type"]),
            name=bragi_response["name"],
            postcodes=postcodes,
            admins=[admin["name"] for admin in bragi_response["administrative_regions"]],
        )

    @staticmethod
    def words(text):
        """
        Split words into a list.

        >>> PlaceFilter.words("17, rue jaune ; Levallois-Peret")
        ['17', 'rue', 'jaune', 'Levallois', 'Peret']
        """
        separators = [" ", "-", ",", ";"]
        return [word for word in re.split("|".join(separators), text) if word]

    @staticmethod
    def word_as_number(word):
        """
        Attempt to intepret the word as a number, potentialy triming a suffix.

        >>> PlaceFilter.word_as_number("17")
        '17'
        >>> PlaceFilter.word_as_number("17bis")
        '17'
        >>> PlaceFilter.word_as_number("17rue") is None
        True
        """
        if word.isnumeric():
            return word

        for suffix in NUM_SUFFIXES:
            if word.lower().endswith(suffix):
                prefix = word[: -len(suffix)]

                if prefix.isnumeric():
                    return prefix

        return None

    @classmethod
    def word_matches(cls, query_word, label_word):
        """
        Check if two words match with an high degree of confidence.

        A single spelling mistake is allowed, defined as either a wrong letter
        (insertion, deletion or replaced) or the inversion of two consecutive
        letters. If an accent is defined in the query, then it must appear in
        the result (or it will count as a spelling mistake).

        Numbers have a special treatment: if word from the query is a number
        (without potential suffix), then it must exactly match the word from
        the result (a number, potentialy with suffix removed).

        >>> PlaceFilter.word_matches("42ter", "42")
        True
        >>> PlaceFilter.word_matches("42ter", "42bis")
        True
        >>> PlaceFilter.word_matches("321", "322")
        False

        >>> PlaceFilter.word_matches("eiffel", "ieffel")
        True
        >>> PlaceFilter.word_matches("eiffel", "ifefel")
        False
        >>> PlaceFilter.word_matches("eveque", "évêque")
        True
        >>> PlaceFilter.word_matches("évêque", "eveque")
        False
        """
        if (query_word_as_num := cls.word_as_number(query_word)) is not None:
            return cls.word_as_number(label_word) == query_word_as_num

        return any(
            damerau_levenshtein_distance(query_word.lower(), s) <= 1
            for s in [label_word.lower(), unidecode(label_word.lower())]
        )

    def filter(self, query):
        if self.type == PlaceType.ADDRESS:
            return self.filter_address(query)

        return self.name.lower() == query.lower()

    def filter_address(self, query):
        query = [
            word
            for word in self.words(query)
            if (len(word) > 2 or word.isnumeric()) and word.lower() not in NUM_SUFFIXES
        ]

        if len(query) <= 2:
            return False

        full_label = [
            *self.words(self.name),
            *self.postcodes,
            *(w for admin in self.admins for w in self.words(admin)),
        ]

        for q_word in query:
            if not any(self.word_matches(q_word, l_word) for l_word in full_label):
                logger.warning(
                    "Removed `%s` from results because queried `%s` does not match the result",
                    self.name,
                    q_word,
                )
                return False

        return True


def build_response(result: InstantAnswerResult, query: str, lang: str):
    return ORJSONResponse(
        InstantAnswerResponse(
            data=InstantAnswerData(result=result, query=InstantAnswerQuery(query=query, lang=lang)),
        ).dict()
    )


def get_instant_answer_single_place(place_id: str, lang: str):
    try:
        place = place_from_id(place_id, follow_redirect=True)
    except Exception as exc:
        logger.warning("Failed to get place for instant answer", exc_info=True)
        raise HTTPException(status_code=404) from exc

    detailed_place = place.load_place(lang=lang)
    return InstantAnswerResult(
        places=[detailed_place],
        source=place.get_source(),
        intention_bbox=None,
        maps_url=maps_urls.get_place_url(place_id),
        maps_frame_url=maps_urls.get_place_url(place_id, no_ui=True),
    )


async def get_instant_answer(
    q: str = Query(..., title="Query string"), lang: str = Query("en", title="Language")
):
    """
    Perform a query with result intended to be displayed as an instant answer
    on *qwant.com*.

    This should not be confused with "Get Places Bbox" as this endpoint will
    run more restrictive checks on its results.
    """
    normalized_query = normalize(q)
    if normalized_query == "":
        if settings["IA_SUCCESS_ON_GENERIC_QUERIES"]:
            result = InstantAnswerResult(
                places=[],
                maps_url=maps_urls.get_default_url(),
                maps_frame_url=maps_urls.get_default_url(no_ui=True),
            )
            return build_response(result, query=q, lang=lang)
        raise NoInstantAnswerToDisplay

    if lang in nlu_allowed_languages:
        try:
            intentions = await nlu_client.get_intentions(text=normalized_query, lang=lang)
        except NluClientException:
            intentions = []
    else:
        intentions = []

    if not intentions:
        bragi_response = await bragi_client.raw_autocomplete(
            {"q": normalized_query, "lang": lang, "limit": 1}
        )
        if len(bragi_response["features"]) > 0:
            place_geocoding = bragi_response["features"][0]["properties"]["geocoding"]
            place_id = place_geocoding["id"]
            place_filter = PlaceFilter.from_bragi_response(place_geocoding)
            if place_filter.filter(normalized_query):
                result = await run_in_threadpool(
                    get_instant_answer_single_place, place_id=place_id, lang=lang
                )
                return build_response(result, query=q, lang=lang)
        raise HTTPException(404)

    intention = intentions[0]
    if not intention.filter.bbox:
        raise HTTPException(404)

    category = intention.filter.category

    places_bbox_response = await get_places_bbox(
        category=[category] if category else [],
        bbox=intention.filter.bbox,
        q=intention.filter.q,
        raw_filter=None,
        source=None,
        size=10,
        lang=lang,
        extend_bbox=True,
    )

    places = places_bbox_response.places
    if len(places) == 0:
        raise HTTPException(404)

    if len(places) == 1:
        place_id = places[0].id
        result = InstantAnswerResult(
            places=places,
            source=places_bbox_response.source,
            intention_bbox=intention.filter.bbox,
            maps_url=maps_urls.get_place_url(place_id),
            maps_frame_url=maps_urls.get_place_url(place_id, no_ui=True),
        )
    else:
        result = InstantAnswerResult(
            places=places,
            source=places_bbox_response.source,
            intention_bbox=intention.filter.bbox,
            maps_url=maps_urls.get_places_url(intention.filter),
            maps_frame_url=maps_urls.get_places_url(intention.filter, no_ui=True),
        )

    return build_response(result, query=q, lang=lang)
