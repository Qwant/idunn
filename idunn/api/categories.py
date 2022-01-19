from pydantic import BaseModel, Field
from typing import List

from idunn.utils.category import Category


class CategoryDescription(BaseModel):
    name: str = Field(..., description="Unique label of the category.")


class AllCategoriesResponse(BaseModel):
    categories: List[CategoryDescription] = Field(..., description="All available categories")


def get_all_categories():
    """List all available categories."""
    return {"categories": [{"name": cat.value} for cat in list(Category)]}
