from .places_list import ALL_CATEGORIES


def get_all_categories():
    categories = []
    for name, category_list in ALL_CATEGORIES.items():
        categories.append({"name": name, "raw_filters": category_list.get("raw_filters")})
    return {"categories": categories}
