import asyncio
import httpx
import logging
import re
from unidecode import unidecode

from idunn.api.places_list import MAX_HEIGHT, MAX_WIDTH
from idunn.api.utils import Category
from idunn.geocoder.models.params import QueryParams as GeocoderParams
from idunn import settings
from idunn.utils.circuit_breaker import IdunnCircuitBreaker
from idunn.utils import result_filter

from .models.geocodejson import Intention
from .bragi_client import bragi_client

logger = logging.getLogger(__name__)

DEFAULT_BBOX_WIDTH = 0.02
DEFAULT_BBOX_HEIGHT = 0.01

NLU_POI_TAGS = ["POI", "other"]
NLU_BRAND_TAGS = ["brand"]
NLU_CATEGORY_TAGS = ["cat"]
NLU_PLACE_TAGS = ["city", "country", "state", "street"]


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
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=0.3, verify=settings["VERIFY_HTTPS"])

    async def post_nlu_classifier(self, text):
        classifier_url = settings["NLU_CLASSIFIER_URL"]
        classifier_domain = settings["NLU_CLASSIFIER_DOMAIN"]
        response_classifier = await self.client.post(
            classifier_url,
            json={"text": text, "domain": classifier_domain, "language": "fr", "count": 1},
        )
        response_classifier.raise_for_status()
        return response_classifier

    async def nlu_classifier(self, text):
        try:
            response_classifier = await classifier_circuit_breaker.call_async(
                self.post_nlu_classifier, text
            )
        except Exception:
            logger.error("Request to NLU classifier failed", exc_info=True)
            return None

        return response_classifier.json()["intention"][0][1]

    @staticmethod
    def regex_classifier(text, is_brand=False):
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
            if is_brand and not cat.match_brand():
                continue
            regex = cat.regex()
            if regex and re.search(regex, normalized_text):
                return cat
        return None

    async def classify_category(self, text, is_brand=False):
        if settings["NLU_CLASSIFIER_URL"] and not is_brand:
            return await self.nlu_classifier(text)
        return self.regex_classifier(text, is_brand=is_brand)

    @classmethod
    def fuzzy_match(cls, query, bragi_res):
        """Does the response match the query reasonably well ?
        >>> NLU_Helper.fuzzy_match("bastille", {"name": "Beuzeville-la-Bastille"})
        False
        >>> NLU_Helper.fuzzy_match("paris 20", {"name": "Paris 20e Arrondissement"})
        True
        >>> NLU_Helper.fuzzy_match(
        ...     "av victor hugo paris",
        ...     {"name": "Avenue Victor Hugo", "administrative_regions": [{"name": "Paris"}]},
        ... )
        True
        """
        q = unidecode(query.strip()).lower()
        if unidecode(bragi_res["name"]).lower().startswith(q):
            return True
        return result_filter.check_bragi_response(q, bragi_res)

    async def build_intention_category_place(
        self,
        cat_query,
        place_query,
        lang,
        is_brand=False,
        extra_geocoder_params=None,
    ):
        async def get_category():
            return await self.classify_category(cat_query, is_brand=is_brand)

        bragi_params = GeocoderParams.build(
            q=place_query,
            lang=lang,
            limit=1,
            **(extra_geocoder_params or {}),
        )

        bragi_result, category = await asyncio.gather(
            bragi_client.autocomplete(bragi_params),
            get_category(),
        )

        if not bragi_result["features"]:
            raise NluClientException("no matching place")

        place = bragi_result["features"][0]
        if not self.fuzzy_match(place_query, place["properties"]["geocoding"]):
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

        if category:
            return Intention(
                filter={"category": category, "bbox": bbox},
                description={"category": category, "place": place},
            )

        return Intention(
            filter={"q": cat_query, "bbox": bbox}, description={"query": cat_query, "place": place}
        )

    async def build_intention_category(self, cat_query, is_brand=False):
        category = await self.classify_category(cat_query, is_brand)

        if category:
            return Intention(filter={"category": category}, description={"category": category})

        return Intention(filter={"q": cat_query}, description={"query": cat_query})

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

    async def get_intentions(self, text, lang, extra_geocoder_params=None) -> [Intention]:
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
            return []

        tags_list = [t for t in response_nlu.json()["NLU"] if t["tag"] != "O"]

        if self.is_poi_request(tags_list):
            logger.info("Detected POI request for '%s'", text, extra=logs_extra)
            return []

        brand_query = self.build_brand_query(tags_list)
        cat_query = self.build_category_query(tags_list)
        place_query = self.build_place_query(tags_list)

        logs_extra["intention_detection"].update(
            {"brand_query": brand_query, "cat_query": cat_query, "place_query": place_query}
        )

        try:
            if brand_query and cat_query:
                raise NluClientException("detected a category and a brand")

            if not brand_query and not cat_query:
                raise NluClientException("no category or brand detected")

            cat_or_brand_query = brand_query or cat_query

            if place_query:
                # 1 category or brand + 1 place
                # Brands are handled the same way categories except that we don't want to process
                # them with the classifier.
                intention = await self.build_intention_category_place(
                    cat_or_brand_query, place_query, lang, bool(brand_query), extra_geocoder_params
                )
            else:
                # 1 category or brand
                intention = await self.build_intention_category(
                    cat_or_brand_query, is_brand=bool(brand_query)
                )

                # A query tagged as "category" and not recognized by the classifier often
                # leads to irrelevant intention. Let's ignore them for now.
                if cat_query and not intention.filter.category:
                    raise NluClientException("no category matched")

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
                }
            )

            if place_props:
                logs_extra["intention_detection"].update(
                    {
                        "res_place_id": place_props.get("id"),
                        "res_place_name": place_props.get("name"),
                    }
                )

            logger.info("Detected intentions for '%s'", text, extra=logs_extra)
            return [intention]
        except NluClientException as exp:
            exp.extra.update(logs_extra)
            raise exp


nlu_client = NLU_Helper()
