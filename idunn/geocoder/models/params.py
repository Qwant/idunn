"""
Bragi parameters as defined here:
  https://github.com/CanalTP/mimirsbrunn/blob/master/libs/bragi/src/routes/autocomplete.rs#L59
"""
import json
from geojson_pydantic.features import Feature
from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel, Field, PositiveInt, confloat, conint
from pydantic.dataclasses import dataclass

from idunn import settings
from idunn.api.utils import Type
from idunn.utils.math import with_precision
from .cosmogony import ZoneType

FOCUS_ZOOM_TO_RADIUS = json.loads(settings["FOCUS_ZOOM_TO_RADIUS"])
FOCUS_MIN_ZOOM = min(zoom for zoom, _, _ in FOCUS_ZOOM_TO_RADIUS)
FOCUS_DECAY = float(settings["FOCUS_DECAY"])


@dataclass
class QueryParams:
    q: str = Query(..., title="Query string")

    lon: Optional[confloat(ge=-180, le=180)] = Query(
        None, title="Longitude", description="Latitude of the focus point."
    )

    lat: Optional[confloat(ge=-90, le=90)] = Query(
        None, title="Latitude", description="Longitude of the focus point."
    )

    zoom: confloat(ge=1) = Query(
        11,
        description=(
            "Zoom level used to compute how far from the focus point results will typically be."
        ),
    )

    lang: Optional[str] = Query(None, title="Language")

    limit: conint(ge=1, le=100) = Query(10, description="Maximum number of results.")

    pt_dataset: List[str] = Query([], description="Point dataset name.")

    poi_dataset: List[str] = Query([], description="POI dataset name.")

    all_data: bool = Query(
        False,
        description=(
            "Search through the entire dataset while ignoring the coverage filter of the geocoder."
        ),
    )

    offset: int = Query(0, ge=0, description="Skip the first results")

    timeout: Optional[int] = Query(
        None, ge=0, title="Timeout: ms", description="Timeout for the queries to the geocoder."
    )

    type: List[Type] = Query([], description="Filter on type of document.")

    zone_type: List[ZoneType] = Query([], description="Filter on type of zone.")

    poi_type: List[str] = Query([], description="Filter on type of POI.")

    nlu: bool = Query(
        bool(settings["AUTOCOMPLETE_NLU_DEFAULT"]),
        description="Perform NLU analysis to extract location and intention from the request.",
    )

    def bragi_query_dict(self):
        """
        Return a dict with parameters accepted by the bragi API
        See https://github.com/CanalTP/mimirsbrunn/blob/v1.14.0/libs/bragi/src/routes/autocomplete.rs#L60
        """
        params = {
            "q": self.q,
            "lang": self.lang,
            "limit": self.limit,
            "pt_dataset[]": self.pt_dataset,
            "poi_dataset[]": self.poi_dataset,
            "all_data": self.all_data,
            "offset": self.offset,
            "timeout": self.timeout,
            "type[]": self.type,
            "zone_type[]": self.zone_type,
            "poi_type[]": self.poi_type,
        }

        # Enables the focus mode
        if self.lon and self.lat and self.zoom and self.zoom >= FOCUS_MIN_ZOOM:
            radius, precision = next(
                (r, p)
                for req_zoom, r, p in sorted(FOCUS_ZOOM_TO_RADIUS, key=lambda l: -l[0])
                if self.zoom >= req_zoom
            )

            params["lon"] = f"{with_precision(self.lon, precision):.2f}"
            params["lat"] = f"{with_precision(self.lat, precision):.2f}"

            # Tune the shape of the weight applied to the results based on the
            # proximity, note that mimir uses an exponential decay:
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html#_supported_decay_functions
            params["proximity_decay"] = f"{FOCUS_DECAY:.2f}"
            params["proximity_offset"] = int(radius / 7.5)
            params["proximity_scale"] = int(6.5 * radius / 7.5)

        return {k: v for k, v in params.items() if v is not None}


class ExtraParams(BaseModel):
    shape: Optional[Feature] = Field(
        None,
        description="Restrict search inside of a polygon given in geojson format.",
        example={
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[2.29, 48.78], [2.34, 48.78], [2.34, 48.81], [2.29, 48.81], [2.29, 48.78]]
                ],
            },
        },
    )
