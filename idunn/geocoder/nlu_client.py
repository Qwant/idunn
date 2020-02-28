import json
import requests
import logging
import re
from collections import Counter
from idunn import settings
from fastapi import HTTPException
from unidecode import unidecode

logger = logging.getLogger(__name__)

from idunn.api.places_list import ALL_CATEGORIES, MAX_HEIGHT, MAX_WIDTH
from idunn.api.pages_jaunes import pj_source
from .models.geocodejson import Intention
from .bragi_client import bragi_client

DEFAULT_BBOX_WIDTH = 0.02
DEFAULT_BBOX_HEIGHT = 0.01


class NLU_Helper:
    def __init__(self):
        self.session = requests.Session()
        if not settings["VERIFY_HTTPS"]:
            self.session.verify = False

    def nlu_classifier(self, text):
        url_classifier = settings["AUTOCOMPLETE_CLASSIFIER_URL"]
        try:
            response_classifier = self.session.post(
                url_classifier,
                data=json.dumps({"text": text, "domain": "poi", "language": "fr", "count": 1}),
                verify=False,
            )
            response_classifier.raise_for_status()
        except Exception:
            logger.error("Request to Classifier returned with unexpected status")
            raise HTTPException(503, "Unexpected NLU error")
        else:
            return response_classifier.json()["intention"][0][1]

    def regex_classifier(self, text):
        normalized_text = unidecode(text).lower().strip()
        for category_name, cat in ALL_CATEGORIES.items():
            regex = cat.get("regex")
            if regex and re.search(regex, normalized_text):
                return category_name
        return None

    def classify_category(self, text):
        if settings["AUTOCOMPLETE_CLASSIFIER_URL"]:
            return self.nlu_classifier(text)
        return self.regex_classifier(text)

    @classmethod
    def fuzzy_match(cls, query, response):
        """ Does the response match the query reasonably well ?
        >>> NLU_Helper.fuzzy_match("bastille", "Beuzeville-la-Bastille")
        False
        >>> NLU_Helper.fuzzy_match("paris 20", "Paris 20e Arrondissement")
        True
        >>> NLU_Helper.fuzzy_match("av victor hugo paris", "Avenue Victor Hugo")
        True
        """
        q = unidecode(query.strip()).lower()
        r = unidecode(response).lower()
        if r[: len(q)] == q:
            # Response starts with query
            return True
        if sum((Counter(r) - Counter(q)).values()) < len(q):
            # Number of missing chars to match the response is low
            # compared to the query length
            return True
        return False

    def build_intention_category_place(self, tags_list, lang):
        category_tag = next(t for t in tags_list if t.get("tag") == "cat")
        city_tag = next(t for t in tags_list if t.get("tag") == "city")
        cat_query = category_tag["phrase"]
        city_query = city_tag["phrase"]

        bragi_result = bragi_client.raw_autocomplete(
            params={"q": city_query, "lang": lang, "limit": 1}
        )
        if not bragi_result["features"]:
            return None

        place = bragi_result["features"][0]
        if not self.fuzzy_match(city_query, place["properties"]["geocoding"]["name"]):
            return None

        bbox = place["properties"]["geocoding"].get("bbox")
        if bbox:
            if bbox[2] - bbox[0] > MAX_WIDTH or bbox[3] - bbox[1] > MAX_HEIGHT:
                return None
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
                return None

        category_name = self.classify_category(cat_query)
        if category_name:
            return Intention(
                filter={"category": category_name, "bbox": bbox},
                description={"category": category_name, "place": place},
            )
        else:
            if not pj_source.bbox_is_covered(bbox):
                return None
            return Intention(
                filter={"q": cat_query, "bbox": bbox},
                description={"query": cat_query, "place": place},
            )

    def build_intention_category(self, tags_list, lang):
        category_tag = next(t for t in tags_list if t.get("tag") == "cat")
        cat_query = category_tag["phrase"]
        category_name = self.classify_category(cat_query)
        if category_name:
            return Intention(
                filter={"category": category_name}, description={"category": category_name},
            )
        return None

    def get_intentions(self, text, lang):
        url_nlu = settings["AUTOCOMPLETE_NLU_URL"]
        # this settings is an immutable string required as a parameter for the NLU API
        params = {"text": text, "lang": lang or settings["DEFAULT_LANGUAGE"], "domain": "poi"}

        try:
            response_nlu = self.session.post(url_nlu, json=params, timeout=0.5)
            response_nlu.raise_for_status()
        except Exception:
            logger.error("Request to NLU returned with unexpected status", exc_info=True)
            return []
        else:
            intentions = []
            tags_list = response_nlu.json()["NLU"]
            tags_list = [t for t in tags_list if t["tag"] != "O"]
            tags_count = Counter(t["tag"] for t in tags_list)
            if tags_count == {"city": 1, "cat": 1}:
                # 1 category + 1 place
                intention = self.build_intention_category_place(tags_list, lang=lang)
                if intention is not None:
                    intentions.append(intention)
            elif tags_count == {"cat": 1}:
                # 1 category
                intention = self.build_intention_category(tags_list, lang=lang)
                if intention is not None:
                    intentions.append(intention)

            return intentions


nlu_client = NLU_Helper()
