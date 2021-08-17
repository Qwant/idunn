from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel
from .base import BaseBlock


class StarsAvailable(Enum):
    YES = "yes"
    NO = "no"

    @classmethod
    def from_bool(cls, val):
        if val:
            return cls.YES

        return cls.NO


class StarsKind(Enum):
    LODGING = "lodging"
    RESTAURANT = "restaurant"


class StarsDetails(BaseModel):
    has_stars: StarsAvailable
    nb_stars: Optional[float]
    kind: StarsKind


class StarsBlock(BaseBlock):
    type: Literal["stars"] = "stars"
    ratings: List[StarsDetails]

    @classmethod
    def from_es(cls, place, lang):
        ratings = [
            StarsDetails(
                has_stars=(
                    StarsAvailable.from_bool(stars)
                    if isinstance(stars, bool)
                    else StarsAvailable.YES
                ),
                nb_stars=stars if isinstance(stars, float) else None,
                kind=kind,
            )
            for kind, stars in [
                (StarsKind.LODGING, place.get_lodging_stars()),
                (StarsKind.RESTAURANT, place.get_restaurant_stars()),
            ]
            if stars is not None
        ]

        if not ratings:
            return None

        return cls(ratings=ratings)
