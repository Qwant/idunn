from datetime import datetime
from typing import Literal, List, Optional
from pydantic import BaseModel, validator
from idunn.utils.thumbr import thumbr

from .base import BaseBlock

MAX_REVIEW_DISPLAY_NUMBER = 3


class Review(BaseModel):
    date: str
    rating: str
    rating_bubble_star_url: str
    url: str
    more_reviews_url: str
    lang: str
    title: str
    text: str
    trip_type: Optional[str]
    author_name: str

    @validator("rating_bubble_star_url", pre=True, always=True)
    def valid_rating_bubble_star_url(cls, rating):
        # Tripadvisor bubble star url need a rating with exactly one decimal point
        # (e.g 4.0 or 4.5)
        rating = f"{float(rating):.1f}"

        base_url = (
            r"https://www.tripadvisor.com/img/cdsi/img2/ratings/traveler/"
            f"s{rating}-MCID-66562.svg"
        )

        if thumbr.is_enabled():
            return thumbr.get_url_remote_thumbnail(base_url)

        return base_url


def build_review(review: dict, source_url: str) -> Review:
    return Review(
        date=review["DatePublished"],
        rating=review["Rating"],
        rating_bubble_star_url=review["Rating"],
        url="".join([source_url, review["ReviewURL"]]),
        more_reviews_url="".join([source_url, review["MoreReviewsURL"]]),
        lang=review["Language"],
        title=review["Title"],
        text=review["Text"],
        trip_type=review["TripType"],
        author_name=review["Author"]["AuthorName"],
    )


class ReviewsBlock(BaseBlock):
    type: Literal["reviews"] = "reviews"
    reviews: List[Review]

    @classmethod
    def build_reviews(cls, reviews: List[dict], source_url: str, lang: str) -> List[Review]:
        lang_order = {lang: 0, "en": 1}
        sorted_reviews = sorted(
            sorted(
                reviews,
                key=lambda x: datetime.strptime(x["DatePublished"][:-5], "%Y-%m-%dT%H:%M:%S.%f"),
                reverse=True,
            ),
            key=lambda x: lang_order.get(x["Language"], 2),
        )
        return [build_review(review, source_url) for review in sorted_reviews[:3]]

    @classmethod
    def from_es(cls, place, lang: str):
        if place.get_reviews() is None:
            return None
        place.get_bubble_star_url(icon=False)
        reviews = cls.build_reviews(place.get_reviews(), place.get_source_url(), lang)
        return cls(reviews=reviews)
