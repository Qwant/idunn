from enum import Enum


class PoiSource(str, Enum):
    OSM = "osm"
    PAGESJAUNES = "pages_jaunes"


ALL_POI_SOURCES = [s.value for s in PoiSource]


WIKIDATA_TO_BBOX_OVERRIDE = {
    # France -> Metropolitan France
    "Q142": [-5.4517733, 41.2611155, 9.8282225, 51.3055721],
    # Tokyo -> Tokyo Metropolis
    "Q1490": [138.9428648, 35.5012219, 139.9213618, 35.8984245],
    # San Francisco: exclude marine reserve
    "Q62": [-122.6164355, 37.7081309, -122.281479, 37.929811],
}
