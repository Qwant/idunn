import json
import requests
import logging
from idunn import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class NLU_Helper:
    def __init__(self):
        self.session = requests.Session()
        self.url_bragi = settings["BRAGI_BASE_URL"] + "/autocomplete"

    def from_classifier(self, text):
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

    def get_intentions(self, params):
        url_nlu = settings["AUTOCOMPLETE_NLU_URL"]
        # this settings is an immutable string required as a parameter for the NLU API
        params["domain"] = "poi"

        try:
            response_nlu = self.session.post(url_nlu, data=params, verify=False, timeout=1)
            response_nlu.raise_for_status()
        except Exception:
            logger.error("Request to NLU returned with unexpected status", exc_info=True)
            return []
        else:
            intentions = []
            tags_list = response_nlu.json()["NLU"]
            category_tags = [t for t in tags_list if t.get("tag") == "category"]
            city_tags = [t for t in tags_list if t.get("tag") == "city"]
            if len(category_tags) > 0 and len(city_tags) > 0:
                category_tag = category_tags[0]
                # TODO: Fetch detail (label, bbox) about city via Bragi
                city_tag = city_tags[0]

                intentions.append(
                    {
                        "type": "category",
                        "category": self.from_classifier(category_tag["phrase"]),
                        "near": {
                            "name": city_tag["phrase"],
                            "label": city_tag["phrase"],
                            "bbox": [0, 0, 0, 0],
                        },
                    }
                )
            return intentions


nlu_client = NLU_Helper()
