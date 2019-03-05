from .places_list import Categories

def get_all_categories():
    categories = []
    for name in Categories.get_categories().keys():
        categories.append(
            {
                "name": name,
                "raw_filters": Categories.get_categories().get(name).get('raw_filters')
            }
        )
    return {
        "categories": categories
    }
