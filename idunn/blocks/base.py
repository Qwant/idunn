import pydantic
from pydantic import BaseModel, conint, constr
from typing import Any, List


class BaseBlock(BaseModel):
    type: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.type:
            raise Exception("Missing type in class %s", self.__class__.__name__)

    @classmethod
    def from_es(cls, es_poi, lang):
        raise NotImplementedError

    @classmethod
    def is_enabled(cls):
        return True
