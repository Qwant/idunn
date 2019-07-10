[1mdiff --git a/idunn/api/places.py b/idunn/api/places.py[m
[1mindex 315d428..1740f31 100644[m
[1m--- a/idunn/api/places.py[m
[1m+++ b/idunn/api/places.py[m
[36m@@ -35,6 +35,7 @@[m [mdef get_place(id, es: Elasticsearch, indices: IndexNames, settings: Settings, la[m
         "addr": Address,[m
         "poi": POI,[m
     }[m
[32m+[m
     loader = places.get(es_place.get('_type'))[m
 [m
     if loader is None:[m
[1mdiff --git a/idunn/api/places_list.py b/idunn/api/places_list.py[m
[1mindex cc1e3ae..a72aab1 100644[m
[1m--- a/idunn/api/places_list.py[m
[1m+++ b/idunn/api/places_list.py[m
[36m@@ -2,7 +2,7 @@[m [mimport os[m
 import logging[m
 import requests[m
 from elasticsearch import Elasticsearch[m
[31m-from apistar.exceptions import BadRequest[m
[32m+[m[32mfrom apistar.exceptions import BadRequest, HTTPException[m
 [m
 from idunn import settings[m
 from idunn.utils.settings import Settings, _load_yaml_file[m
[36m@@ -23,8 +23,7 @@[m [mlogger = logging.getLogger(__name__)[m
 MAX_WIDTH = 1.0 # max bbox longitude in degrees[m
 MAX_HEIGHT = 1.0  # max bbox latitude in degrees[m
 [m
[31m-KUZZLE_CLUSTER_ADDRESS = 'KUZZLE_CLUSTER_ADDRESS'[m
[31m-KUZZLE_CLUSTER_PORT = 'KUZZLE_CLUSTER_PORT'[m
[32m+[m
 SOURCE_OSM = 'osm'[m
 SOURCE_PAGESJAUNES = 'pagesjaunes'[m
 ALL_SOURCES = [SOURCE_OSM, SOURCE_PAGESJAUNES][m
[36m@@ -193,15 +192,15 @@[m [mdef get_places_bbox(bbox, es: Elasticsearch, indices: IndexNames, settings: Sett[m
 [m
 [m
 def get_events_bbox(bbox, query_params: http.QueryParams):[m
[31m-    raw_params = get_raw_params(query_params)[m
[31m-    kuzzle_address = settings.get(KUZZLE_CLUSTER_ADDRESS)[m
[31m-    kuzzle_port = settings.get(KUZZLE_CLUSTER_PORT)[m
[32m+[m[32m    # raw_params = get_raw_params(query_params)[m
[32m+[m[32m    kuzzle_address = settings.get('KUZZLE_CLUSTER_ADDRESS')[m
[32m+[m[32m    kuzzle_port = settings.get('KUZZLE_CLUSTER_PORT')[m
 [m
     if not kuzzle_address or not kuzzle_port:[m
[31m-        raise Exception(f"Missing kuzzle address or port: (port {KUZZLE_CLUSTER_PORT} is not set or address ${KUZZLE_CLUSTER_ADDRESS} is not set")[m
[32m+[m[32m        raise HTTPException(f"Missing kuzzle address or port", status_code=501)[m
 [m
     try:[m
[31m-        params = EventQueryParam(**raw_params)[m
[32m+[m[32m        params = EventQueryParam(**query_params)[m
     except ValidationError as e:[m
         logger.warning(f"Validation Error: {e.json()}")[m
         raise BadRequest([m
[1mdiff --git a/idunn/api/urls.py b/idunn/api/urls.py[m
[1mindex 4a6a1d4..6d84c76 100644[m
[1m--- a/idunn/api/urls.py[m
[1m+++ b/idunn/api/urls.py[m
[36m@@ -25,5 +25,5 @@[m [mdef get_api_urls(settings):[m
         Route('/places/{id}', 'GET', handler=get_place),[m
         Route('/categories', 'GET', handler=get_all_categories),[m
         Route('/places', 'GET', handler=get_places_bbox),[m
[31m-        Route('/events', 'GET', handler=get_events_bbox)[m
[32m+[m[32m        Route('/events', 'GET', handler=get_events_bbox),[m
     ][m
[1mdiff --git a/idunn/blocks/events.py b/idunn/blocks/events.py[m
[1mindex b8f5e82..105097a 100644[m
[1m--- a/idunn/blocks/events.py[m
[1m+++ b/idunn/blocks/events.py[m
[36m@@ -6,8 +6,8 @@[m [mfrom .base import BaseBlock[m
 class OpeningDayEvent(BaseBlock):[m
     BLOCK_TYPE = "event_opening_date"[m
 [m
[31m-    date_start = validators.String()[m
[31m-    date_end = validators.String()[m
[32m+[m[32m    date_start = validators.DateTime()[m
[32m+[m[32m    date_end = validators.DateTime()[m
     space_time_info = validators.String(allow_null=True)[m
     timetable = validators.Array(allow_null=True)[m
 [m
[36m@@ -20,12 +20,12 @@[m [mclass OpeningDayEvent(BaseBlock):[m
 [m
         if isinstance(timetable, str):[m
             timetable = timetable.split(';')[m
[31m-            test = [][m
[32m+[m[32m            new_format_timetable = [][m
             for tt in timetable:[m
                 date_start_end = tt.split(' ')[m
[31m-                test.append({ 'begin': date_start_end[0], 'end': date_start_end[1]})[m
[32m+[m[32m                new_format_timetable.append({ 'begin': date_start_end[0], 'end': date_start_end[1]})[m
 [m
[31m-            timetable = test[m
[32m+[m[32m            timetable = new_format_timetable[m
         if not (date_start or date_end or space_time_info or timetable):[m
             return None[m
 [m
[1mdiff --git a/idunn/places/event.py b/idunn/places/event.py[m
[1mindex d5382c2..d1fd0e7 100644[m
[1m--- a/idunn/places/event.py[m
[1m+++ b/idunn/places/event.py[m
[36m@@ -21,8 +21,8 @@[m [mclass Event(BasePlace):[m
     def get_coord(self):[m
         return self.get('geo_loc')[m
 [m
[31m-    def get_lang(self):[m
[31m-        return self.get('lang')[m
[32m+[m[32m    # def get_lang(self):[m
[32m+[m[32m    #   return self.get('lang')[m
 [m
     def get_website(self):[m
         return self.get('link')[m
