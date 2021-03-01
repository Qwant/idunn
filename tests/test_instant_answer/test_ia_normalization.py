from idunn.instant_answer import normalize


def test_normalization():
    assert normalize("Strasbourg") == "strasbourg"
    assert normalize("map Strasbourg") == "strasbourg"
    assert normalize("strasbourg maps") == "strasbourg"
    assert normalize("horaires musée picasso") == "musée picasso"
    assert normalize("mapabcd") == "mapabcd"
    assert normalize("prendre rdv dentiste rennes") == "dentiste rennes"
    assert normalize("où se situe Limoges") == "limoges"
    assert normalize("ou se trouve la tour Eiffel") == "tour eiffel"
    assert normalize("qwantmaps") == ""
    assert normalize("Restaurants lille avis") == "restaurants lille"
    assert normalize("hotel bordeaux booking") == "hotel bordeaux"
