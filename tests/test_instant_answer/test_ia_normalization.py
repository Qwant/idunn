from idunn.services.instant_answer.normalization import normalize_instant_answer_param


def test_normalization():
    assert normalize_instant_answer_param("Strasbourg", "fr") == ("strasbourg", "fr")
    assert normalize_instant_answer_param("map Strasbourg", "fr") == ("strasbourg", "fr")
    assert normalize_instant_answer_param("strasbourg maps", "fr") == ("strasbourg", "fr")
    assert normalize_instant_answer_param("horaires musée picasso", "fr") == ("musée picasso", "fr")
    assert normalize_instant_answer_param("mapabcd", "fr") == ("mapabcd", "fr")
    assert normalize_instant_answer_param("prendre rdv dentiste rennes", "fr") == (
        "dentiste rennes",
        "fr",
    )
    assert normalize_instant_answer_param("où se situe Limoges", "fr") == ("limoges", "fr")
    assert normalize_instant_answer_param("ou se trouve la tour Eiffel", "fr") == (
        "tour eiffel",
        "fr",
    )
    assert normalize_instant_answer_param("qwantmaps", "fr") == ("", "fr")
    assert normalize_instant_answer_param("Restaurants lille avis", "fr") == (
        "restaurants lille",
        "fr",
    )
    assert normalize_instant_answer_param("hotel bordeaux booking", "fr") == (
        "hotel bordeaux",
        "fr",
    )
