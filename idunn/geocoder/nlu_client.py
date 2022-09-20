import httpx
import logging
import re
from typing import Optional
from unidecode import unidecode

from idunn.api.places_list import MAX_HEIGHT, MAX_WIDTH
from idunn.geocoder.models.params import QueryParams as GeocoderParams
from idunn import settings
from idunn.utils.circuit_breaker import IdunnCircuitBreaker
from idunn.utils.result_filter import ResultFilter

from .models.geocodejson import Intention, IntentionType
from .bragi_client import bragi_client
from ..utils.category import Category

logger = logging.getLogger(__name__)
result_filter = ResultFilter()

DEFAULT_BBOX_WIDTH = 0.02
DEFAULT_BBOX_HEIGHT = 0.01

NLU_POI_TAGS = ["POI", "other"]
NLU_BRAND_TAGS = ["brand"]
NLU_CATEGORY_TAGS = ["cat"]
NLU_PLACE_TAGS = ["city", "country", "state", "street"]
NLU_STREET_TAGS = ["street"]


class NluClientException(Exception):
    def __init__(self, reason):
        self.extra = {"reason": reason}
        super().__init__(f"No result from NLU client, reason: `{self.reason()}`")

    def reason(self):
        return self.extra["reason"]


tagger_circuit_breaker = IdunnCircuitBreaker(
    "nlu_tagger_api_breaker",
    int(settings["NLU_BREAKER_MAXFAIL"]),
    int(settings["NLU_BREAKER_TIMEOUT"]),
)

classifier_circuit_breaker = IdunnCircuitBreaker(
    "classifier_tagger_api_breaker",
    int(settings["NLU_BREAKER_MAXFAIL"]),
    int(settings["NLU_BREAKER_TIMEOUT"]),
)


class NLU_Helper:  # pylint: disable = invalid-name
    CLASSIF_MIN_UNK_IGNORED = float(settings["NLU_CLASSIFIER_MIN_UNK_IGNORED"])
    CLASSIF_CATEGORY_MIN_WEIGHT = float(settings["NLU_CLASSIFIER_CATEGORY_MIN_WEIGHT"])
    CLASSIF_MAX_WEIGHT_RATIO = float(settings["NLU_CLASSIFIER_MAX_WEIGHT_RATIO"])

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=float(settings["NLU_CLIENT_TIMEOUT"]), verify=settings["VERIFY_HTTPS"]
        )

    async def post_nlu_classifier(self, text):
        classifier_url = settings["NLU_CLASSIFIER_URL"]
        classifier_domain = settings["NLU_CLASSIFIER_DOMAIN"]
        response_classifier = await self.client.post(
            classifier_url,
            json={
                "text": text,
                "domain": classifier_domain,
                "language": "fr",
                "count": 10,
            },
        )
        response_classifier.raise_for_status()
        return response_classifier

    @classmethod
    def nlu_classifier_handle_response(cls, response) -> Optional[Category]:
        """
        Analyze raw classifier response to find an unambiguous category from
        its result if any.

        >>> NLU_Helper.nlu_classifier_handle_response({
        ...     "intention": [(0.95, "restaurant"), (0.01, "cinema")],
        ... }).value
        'restaurant'
        >>> NLU_Helper.nlu_classifier_handle_response({
        ...     "intention": [(0.02, "restaurant"), (0.01, "cinema")],
        ... }) is None
        True
        """
        categories = {cat: weight for weight, cat in response["intention"]}

        if (
            # The classifier puts high probability to be unclassified ("unk").
            categories.pop("unk", 0) >= cls.CLASSIF_MIN_UNK_IGNORED
            # No category found by the classifier.
            or not categories
        ):
            return None

        best, max_weight = max(categories.items(), key=lambda x: x[1])
        del categories[best]

        if (
            # There is no category with a fair probability.
            max_weight < cls.CLASSIF_CATEGORY_MIN_WEIGHT
            # There is at least one category with a weight close to the best one.
            or (categories and max(categories.values()) > cls.CLASSIF_MAX_WEIGHT_RATIO * max_weight)
        ):
            return None

        return Category.__members__.get(best)

    async def nlu_classifier(self, text) -> Optional[Category]:
        try:
            response_classifier = await classifier_circuit_breaker.call_async(
                self.post_nlu_classifier, text
            )
        except Exception:
            logger.error("Request to NLU classifier failed", exc_info=True)
            return None

        return self.nlu_classifier_handle_response(response_classifier.json())

    @staticmethod
    def regex_classifier(text) -> Optional[Category]:
        """Match text with a category, using 'regex'
        >>> NLU_Helper.regex_classifier("restau").value
        'restaurant'
        >>> NLU_Helper.regex_classifier("pub").value
        'bar'
        >>> NLU_Helper.regex_classifier("republique") is None
        True
        """
        normalized_text = unidecode(text).lower().strip()
        for cat in list(Category):
            regex = cat.regex()
            if regex and re.search(regex, normalized_text):
                return cat
        return None

    async def classify_category(self, text):
        return await self.nlu_classifier(text) or self.regex_classifier(text)

    @classmethod
    def fuzzy_match(cls, query, bragi_res):
        """Does the response match the query reasonably well ?
        >>> NLU_Helper.fuzzy_match(
        ...     "bastille",
        ...     {"properties": {"geocoding": {"name": "Beuzeville-la-Bastille"}}},
        ... )
        False
        >>> NLU_Helper.fuzzy_match(
        ...     "paris 20",
        ...     {"properties": {"geocoding": {"name": "Paris 20e Arrondissement"}}},
        ... )
        True
        >>> NLU_Helper.fuzzy_match(
        ...     "av victor hugo paris",
        ...     {
        ...         "properties": {
        ...             "geocoding": {
        ...                 "name": "Avenue Victor Hugo",
        ...                 "administrative_regions": [{"name": "Paris"}],
        ...             },
        ...         },
        ...     },
        ... )
        True
        """
        q = unidecode(query.strip()).lower()
        if unidecode(bragi_res["properties"]["geocoding"]["name"]).lower().startswith(q):
            return True
        return bool(result_filter.filter_bragi_features(q, [bragi_res]))

    async def get_bbox_place(self, bragi_result, place_query):
        if not bragi_result["features"]:
            raise NluClientException("no matching place")
        place = bragi_result["features"][0]
        if not self.fuzzy_match(place_query, place):
            raise NluClientException("matching place too different from query")
        bbox = place["properties"]["geocoding"].get("bbox")
        if bbox:
            if bbox[2] - bbox[0] > MAX_WIDTH or bbox[3] - bbox[1] > MAX_HEIGHT:
                raise NluClientException("matching place is too large")
        else:
            geometry = place.get("geometry", {})
            if geometry.get("type") == "Point":
                lon, lat = geometry.get("coordinates")
                bbox = [
                    lon - DEFAULT_BBOX_WIDTH / 2,
                    lat - DEFAULT_BBOX_HEIGHT / 2,
                    lon + DEFAULT_BBOX_WIDTH / 2,
                    lat + DEFAULT_BBOX_HEIGHT / 2,
                ]
            else:
                raise NluClientException("matching place has no coordinates")
        return bbox, place

    async def build_intention_category(self, cat_query):
        category = await self.classify_category(cat_query)

        if category:
            return Intention(
                type=IntentionType.CATEGORY,
                filter={"q": cat_query, "category": category},
                description={"category": category},
            )

        return Intention(
            type=IntentionType.BRAND,
            filter={"q": cat_query},
            description={"query": cat_query},
        )

    @classmethod
    def is_poi_request(cls, tags_list):
        """Check if a request is addressed to a POI"""
        return any(t.get("tag") in NLU_POI_TAGS for t in tags_list)

    @classmethod
    def build_brand_query(cls, tags_list):
        tags = [t["phrase"] for t in tags_list if t.get("tag") in NLU_BRAND_TAGS]

        if len(tags) >= 2:
            raise NluClientException("multiple brand labels")

        return next(iter(tags), None)

    @classmethod
    def build_category_query(cls, tags_list):
        tags = [t["phrase"] for t in tags_list if t.get("tag") in NLU_CATEGORY_TAGS]

        if len(tags) >= 2:
            raise NluClientException("multiple category labels")

        return next(iter(tags), None)

    @classmethod
    def build_place_query(cls, tags_list):
        tags = [t["phrase"] for t in tags_list if t.get("tag") in NLU_PLACE_TAGS]

        if not tags:
            return None

        return " ".join(tags)

    async def post_intentions(self, text, lang):
        tagger_url = settings["NLU_TAGGER_URL"]
        tagger_domain = settings["NLU_TAGGER_DOMAIN"]
        # this settings is an immutable string required as a parameter for the NLU API
        params = {
            "text": text,
            "lang": lang or settings["DEFAULT_LANGUAGE"],
            "domain": tagger_domain,
            "detok": True,  # preserve the non-tokenized query in tagged chunks
            "lowercase": settings["NLU_TAGGER_LOWERCASE"],
        }
        response_nlu = await self.client.post(tagger_url, json=params)
        response_nlu.raise_for_status()
        return response_nlu

    async def get_intention(
        self,
        text,
        lang,
        extra_geocoder_params=None,
        allow_types=[IntentionType.BRAND, IntentionType.CATEGORY],
    ) -> Optional[Intention]:
        """
        Get the intention with an associated bbox when a place is found in the query
        """
        logs_extra = {
            "intention_detection": {
                "text": text,
                "lang": lang,
                "extra_geocoder_params": extra_geocoder_params,
            }
        }

        try:
            response_nlu = await tagger_circuit_breaker.call_async(self.post_intentions, text, lang)
        except Exception:
            logger.error("Request to NLU tagger failed", exc_info=True, extra=logs_extra)
            return None

        tags_list = [t for t in response_nlu.json()["NLU"] if t["tag"] != "O"]

        try:
            place_query = self.build_place_query(tags_list)
            brand_query = self.build_brand_query(tags_list)
            cat_query = self.build_category_query(tags_list)

            if self.is_poi_request(tags_list):
                if IntentionType.POI not in allow_types:
                    logger.info("Detected POI request for '%s'", text, extra=logs_extra)
                    return None

                intention = Intention(
                    type=IntentionType.POI,
                    filter={"q": text},
                    description={"query": text},
                )

                intention.description._place_in_query = any(
                    t.get("tag") in NLU_PLACE_TAGS for t in tags_list
                )
            else:
                if brand_query and cat_query:
                    raise NluClientException("detected a category and a brand")

                if not brand_query and not cat_query:
                    raise NluClientException("no category or brand detected")

                cat_or_brand_query = brand_query or cat_query

                intention = await self.build_intention_category(cat_or_brand_query)

                self.add_extra_logs(brand_query, cat_query, intention, logs_extra, place_query)
                logger.info("Detected intentions for '%s'", text, extra=logs_extra)
            if place_query:
                bbox, place = await self.get_place_and_bbox_from_query(
                    extra_geocoder_params, lang, place_query
                )
                intention.filter.bbox = bbox
                intention.description.place = place
            else:
                if cat_query and not intention.filter.category:
                    raise NluClientException("no category matched")
            return intention

        except NluClientException as exp:
            exp.extra.update(logs_extra)
            raise exp

    async def get_place_and_bbox_from_query(self, extra_geocoder_params, lang, place_query):
        bragi_params = GeocoderParams.build(
            q=place_query,
            lang=lang,
            limit=1,
            **(extra_geocoder_params or {}),
        )
        bragi_result = await bragi_client.autocomplete(bragi_params)
        return await self.get_bbox_place(bragi_result, place_query)

    @staticmethod
    def add_extra_logs(brand_query, cat_query, intention, logs_extra, place_query):
        intention_dict = intention.dict(exclude_none=True)
        place_props = (
            intention_dict.get("description", {})
            .get("place", {})
            .get("properties", {})
            .get("geocoding", {})
        )
        logs_extra["intention_detection"].update(
            {
                "res_category": intention_dict.get("filter", {}).get("category"),
                "res_bbox": intention_dict.get("filter", {}).get("bbox"),
                "res_query": intention_dict.get("filter", {}).get("q"),
                "brand_query": brand_query,
                "cat_query": cat_query,
                "place_query": place_query,
            }
        )
        if place_props:
            logs_extra["intention_detection"].update(
                {
                    "res_place_id": place_props.get("id"),
                    "res_place_name": place_props.get("name"),
                }
            )


nlu_client = NLU_Helper()
