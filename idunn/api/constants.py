from enum import Enum


class PoiSource(str, Enum):
    OSM = "osm"
    PAGESJAUNES = "pages_jaunes"


ALL_POI_SOURCES = [s.value for s in PoiSource]
