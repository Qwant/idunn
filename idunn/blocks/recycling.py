from .base import BaseBlock

from typing import ClassVar

from idunn import settings

import requests

class RecyclingBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "recycling"

    volume: float
    last_update: str

    @classmethod
    def from_es(cls, es_poi, lang):
        if not es_poi.get_recycling() or settings.get("RECYCLING_SERVER_URL") is None:
            return None
        server_url = settings["RECYCLING_SERVER_URL"]
        if not server_url.endswith('/'):
            server_url += '/'
        try:
            args = {}
            if settings.get("KUZZLE_REQUEST_TIMEOUT") is not None:
                args["timeout"] = float(settings["KUZZLE_REQUEST_TIMEOUT"])
            res = requests.get(f"{server_url}{es_poi.get_id()}", **args)
            res = res.json()
            trash_volume = res.get("result", {}).get("_source", {}).get("volume")
            if trash_volume is None:
                return None
            trash_volume = float(trash_volume)
            trash_last_update = res.get("result", {}).get("_source", {}).get("hour")
        except Exception as e:
            # TODO: use logger
            print(f"failed to get information for trash {es_poi.get_id()}: {e}")
            return None
        return cls(volume=trash_volume, last_update=trash_last_update)
