from idunn import settings
from idunn.places import POI, Place
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.datasources.mimirsbrunn import fetch_es_poi


def get_poi(id: str, lang: str = None) -> Place:
    """Handler that returns points-of-interest"""
    es = get_elasticsearch()
    if not lang:
        lang = settings["DEFAULT_LANGUAGE"]
    lang = lang.lower()

    es_poi = fetch_es_poi(id, es)
    return POI(es_poi).load_place(lang)
