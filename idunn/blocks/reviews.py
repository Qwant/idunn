from typing import Literal, Optional, List

from .base import BaseBlock


class Review:
    date: Optional[str]
    url: Optional[str]
    lang: Optional[str]
    title: Optional[str]
    text: Optional[str]
    trip_type: Optional[str]
    author_name: Optional[str]


class ReviewsBlock(BaseBlock):
    type: Literal["reviews"] = "reviews"
    reviews: List[Review]

    @classmethod
    def from_es(cls, place, lang):
        return cls(
            reviews=place.get_reviews() or None,
        )
