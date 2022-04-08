from typing import Literal, List
from pydantic import BaseModel

from .base import BaseBlock


class Review(BaseModel):
    date: str
    url: str
    lang: str
    title: str
    text: str
    trip_type: str
    author_name: str


class ReviewsBlock(BaseBlock):
    type: Literal["reviews"] = "reviews"
    reviews: List[Review]

    @classmethod
    def build_reviews(cls, place):
        reviews = []
        for review_dict in place.get_reviews():
            reviews.append(
                Review(
                    date=review_dict["DatePublished"],
                    url="".join([place.get_source_url(), review_dict["ReviewURL"]]),
                    lang=review_dict["Language"],
                    title=review_dict["Title"],
                    text=review_dict["Text"],
                    trip_type=review_dict["TripType"],
                    author_name=review_dict["Author"]["AuthorName"],
                )
            )
        return reviews

    @classmethod
    def from_es(cls, place, lang):
        print(place)
        return cls(
            reviews=cls.build_reviews(place) or None,
        )
