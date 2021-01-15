from pydantic import BaseModel
from typing import Any


class BaseBlock(BaseModel):
    type: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.type:
            raise Exception(f"Missing type in class {self.__class__.__name__}")

    @classmethod
    def from_es(cls, es_poi, lang):
        raise NotImplementedError

    @classmethod
    def is_enabled(cls):
        return True
