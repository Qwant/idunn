from .base import BaseBlock

from typing import ClassVar, Union, Optional

from pydantic import BaseModel


class WebsiteUrl(BaseModel):
    url: str
    redirect: bool = False
    hash: Optional[str]
    label: Optional[str]


class WebSiteBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "website"

    url: Union[str, WebsiteUrl]

    @classmethod
    def from_es(cls, es_poi, lang):
        website = es_poi.get_website()
        if not website:
            return None
        return cls(url=website)
