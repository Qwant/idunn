import os
from enum import Enum

from idunn.datasources.mimirsbrunn import MimirPoiFilter
from idunn.utils.settings import _load_yaml_file


def get_categories():
    categories_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../utils/categories.yml"
    )
    return _load_yaml_file(categories_path)["categories"]


ALL_CATEGORIES = get_categories()


class CategoryEnum(str):
    """
    Methods defining the behavior of the enum `Category` defined bellow.
    """

    def pj_what(self):
        return ALL_CATEGORIES[self].get("pj_what")

    def raw_filters(self) -> [MimirPoiFilter]:
        raw_filters = ALL_CATEGORIES[self].get("raw_filters")
        filters = []
        for f in raw_filters:
            f = f.copy()
            filters.append(MimirPoiFilter(properties=f))
        return filters

    def regex(self):
        return ALL_CATEGORIES[self].get("regex")


# Load the list of categories as an enum for validation purpose
Category = Enum("Category", {cat: cat for cat in ALL_CATEGORIES}, type=CategoryEnum)
