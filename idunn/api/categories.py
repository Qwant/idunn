from .utils import Category
from pydantic import BaseModel, Field
from typing import List


class CategoryDescription(BaseModel):
    name: str = Field(..., description="Unique label of the category.")
    raw_filters: List[str] = Field(..., description="Raw filter on OSM tags.")


class AllCategoriesResponse(BaseModel):
    categories: List[CategoryDescription] = Field(..., description="All available categories")


def get_all_categories() -> AllCategoriesResponse:
    """List all available categories."""
    return {
        "categories": [
            {"name": cat.value, "raw_filters": cat.raw_filters()} for cat in list(Category)
        ]
    }
