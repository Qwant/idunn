import logging
from fastapi import HTTPException
from elasticsearch7 import ElasticsearchException
from idunn import settings
from idunn.utils.es_wrapper import get_elasticsearch
from idunn.utils.index_names import INDICES
from idunn.places.exceptions import PlaceNotFound

logger = logging.getLogger(__name__)

PLACE_DEFAULT_INDEX = settings["PLACE_DEFAULT_INDEX"]
PLACE_POI_INDEX = settings["PLACE_POI_INDEX"]
PLACE_ADDRESS_INDEX = settings["PLACE_ADDRESS_INDEX"]
PLACE_STREET_INDEX = settings["PLACE_STREET_INDEX"]

is_es2 = settings["MIMIR_ES_VERSION"] == "2"


class MimirPoiFilter:
    def __init__(self, poi_class=None, poi_subclass=None, extra=None):
        self.poi_class = poi_class
        self.poi_subclass = poi_subclass
        self.extra = extra or {}

    def get_terms_filters(self):
        terms = []
        if self.poi_class:
            terms.append(f"class_{self.poi_class}")
        if self.poi_subclass:
            terms.append(f"subclass_{self.poi_subclass}")
        for key, value in self.extra.items():
            terms.append(f"{key}:{value}")
        return terms

    @classmethod
    def from_url_raw_filter(cls, raw_filter):
        poi_class, poi_subclass = raw_filter.split(",", maxsplit=1)
        if poi_class == "*":
            poi_class = None
        if poi_subclass == "*":
            poi_subclass = None
        return cls(poi_class, poi_subclass)


def fetch_es_pois(filters: [MimirPoiFilter], bbox, max_size) -> list:
    es = get_elasticsearch()
    left, bot, right, top = bbox[0], bbox[1], bbox[2], bbox[3]

    should_terms = []
    for f in filters:
        terms = f.get_terms_filters()
        if terms == []:
            should_terms.append({"match_all": {}})
        else:
            should_terms.append(
                {"bool": {"must": [{"term": {"poi_type.name": term}} for term in terms]}}
            )

    # pylint: disable = unexpected-keyword-arg
    bbox_places = es.search(
        index=INDICES["poi"],
        query={
            "bool": {
                "should": should_terms,
                "minimum_should_match": 1,
                "filter": {
                    "geo_bounding_box": {
                        "coord": {
                            "top_left": {"lat": top, "lon": left},
                            "bottom_right": {"lat": bot, "lon": right},
                        }
                    }
                },
            }
        },
        sort={"weight": "desc"},
        size=max_size,
        timeout="3s",
        ignore_unavailable=True,
    )

    bbox_places = bbox_places.get("hits", {}).get("hits", [])
    return bbox_places


def fetch_es_place(id, es, type) -> dict:
    """Returns the raw Place data

    This function gets from Elasticsearch the
    entry corresponding to the given id.
    """
    if type is None:
        index_name = PLACE_DEFAULT_INDEX
    elif type not in INDICES:
        raise HTTPException(status_code=400, detail=f"Wrong type parameter: type={type}")
    else:
        index_name = INDICES.get(type)

    if is_es2:
        extra_search_params = {"_source_exclude": "boundary"}
    else:
        extra_search_params = {"_source_excludes": "boundary"}

    try:
        es_places = es.search(
            index=index_name,
            query={"bool": {"filter": {"term": {"_id": id}}}},
            ignore_unavailable=True,
            **extra_search_params,
        )
    except ElasticsearchException as error:
        logger.warning("error with database: %s", error)
        raise HTTPException(detail="database issue", status_code=503) from error

    es_place = es_places.get("hits", {}).get("hits", [])
    if len(es_place) == 0:
        if type is None:
            message = f"place '{id}' not found"
        else:
            message = f"place '{id}' not found with type={type}"
        raise PlaceNotFound(message=message)
    if len(es_place) > 1:
        logger.warning("Got multiple places with id %s", id)

    return es_place[0]


def fetch_closest(lat, lon, max_distance, es):
    es_addrs = es.search(
        index=",".join([PLACE_ADDRESS_INDEX, PLACE_STREET_INDEX]),
        from_=0,
        size=1,
        query={
            "function_score": {
                "query": {
                    "bool": {
                        "filter": {
                            "geo_distance": {
                                "distance": "{}m".format(max_distance),
                                "coord": {"lat": lat, "lon": lon},
                                "distance_type": "plane",
                            }
                        }
                    }
                },
                "boost_mode": "replace",
                "functions": [
                    {
                        "gauss": {
                            "coord": {
                                "origin": {"lat": lat, "lon": lon},
                                "scale": "{}m".format(max_distance),
                            }
                        }
                    }
                ],
            }
        },
    )
    es_addrs = es_addrs.get("hits", {}).get("hits", [])
    if len(es_addrs) == 0:
        raise HTTPException(
            status_code=404, detail=f"nothing around {lat}:{lon} within {max_distance}m..."
        )
    return es_addrs[0]


def fetch_es_poi(id, es) -> dict:
    """Returns the raw POI data
    @deprecated by fetch_es_place()

    This function gets from Elasticsearch the
    entry corresponding to the given id.
    """
    try:
        return fetch_es_place(id, es, type="poi")["_source"]
    except PlaceNotFound as e:
        raise HTTPException(status_code=404, detail=e.message) from e
