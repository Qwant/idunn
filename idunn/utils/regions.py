import json
import os
from typing import Tuple


DIR = os.path.dirname(__file__)
REGIONS_FILE = os.path.join(DIR, "data/regions.json")
REGIONS = json.load(open(REGIONS_FILE))


def get_region_lonlat(region: str) -> Tuple[float, float]:
    """
    Return the center coordinates for a given region code.

    >>> assert get_region_lonlat("unknown") is None
    >>> get_region_lonlat("fr")
    (2.3514616, 48.856696899999996)
    """
    region = region.upper()
    latlon = REGIONS.get(region, {}).get("center", None)

    if latlon is None:
        return None

    return tuple(latlon)
