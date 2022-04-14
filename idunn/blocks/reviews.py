from datetime import datetime
from typing import Literal, List, Optional
from pydantic import BaseModel

from .base import BaseBlock

MAX_REVIEW_DISPLAY_NUMBER = 3


class Review(BaseModel):
    date: str
    rating: str
    url: str
    more_reviews_url: str
    lang: str
    title: str
    text: str
    trip_type: Optional[str]
    author_name: str


def build_review(review: dict, source_url: str) -> Review:
    return Review(
        date=review["DatePublished"],
        rating=review["Rating"],
        url="".join([source_url, review["ReviewURL"]]),
        more_reviews_url="".join([source_url, review["MoreReviewsURL"]]),
        lang=review["Language"],
        title=review["Title"],
        text=review["Text"],
        trip_type=review["TripType"],
        author_name=review["Author"]["AuthorName"],
    )


def find_reviews_with_specific_lang(
    reviews: List[dict], lang: str, source_url: str
) -> List[Review]:
    reviews_lang = list(filter(lambda x: x["Language"] == lang, reviews))
    reviews_lang.sort(
        key=lambda x: datetime.strptime(x["DatePublished"][:-5], "%Y-%m-%dT%H:%M:%S.%f"),
        reverse=True,
    )
    return [build_review(review, source_url) for review in reviews_lang]


def find_other_reviews(reviews: List[dict], lang: str, source_url: str) -> List[Review]:
    reviews_lang = list(filter(lambda x: x["Language"] not in [lang, "en"], reviews))
    reviews_lang.sort(
        key=lambda x: datetime.strptime(x["DatePublished"][:-5], "%Y-%m-%dT%H:%M:%S.%f"),
        reverse=True,
    )
    return [build_review(review, source_url) for review in reviews_lang]


class ReviewsBlock(BaseBlock):
    type: Literal["reviews"] = "reviews"
    reviews: List[Review]

    @classmethod
    def build_reviews(cls, reviews: List[dict], source_url: str, lang: str) -> List[Review]:
        sorted_reviews = []
        sorted_reviews.extend(find_reviews_with_specific_lang(reviews, lang, source_url))
        if len(sorted_reviews) < MAX_REVIEW_DISPLAY_NUMBER:
            sorted_reviews.extend(find_reviews_with_specific_lang(reviews, "en", source_url))
        if len(sorted_reviews) < MAX_REVIEW_DISPLAY_NUMBER:
            sorted_reviews.extend(find_other_reviews(reviews, lang, source_url))
        return sorted_reviews[:3]

    @classmethod
    def from_es(cls, place, lang: str):
        if place.get_reviews() is None:
            return None
        reviews = cls.build_reviews(place.get_reviews(), place.get_source_url(), lang)
        return cls(reviews=reviews)
