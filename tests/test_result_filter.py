from idunn.utils.result_filter import ResultFilter


def test_filter():
    filter = ResultFilter()

    place_infos = {
        "names": ["5 rue Gustave Zédé", "5, Zédéstraße"],
        "postcodes": ["79000"],
        "place_type": "house",
    }

    # Case is ignored
    assert filter.check("5 RuE gustave ZÉDÉ", **place_infos)

    # Extra terms are not allowed
    assert not filter.check("5 rue gustave zédé restaurant", **place_infos)

    # Numbers must match
    assert not filter.check("1 rue gustave zédé", **place_infos)
    assert not filter.check("5 rue gustave zédé 75015", **place_infos)

    # Accents can be omitted
    assert filter.check("5 rue gustave zede", **place_infos)

    # Accents in the request still matter
    assert not filter.check("5 rue güstâve zédé", **place_infos)

    # A single spelling mistake is allowed per word
    assert filter.check("5 ruee gustaev zde", **place_infos)
    assert not filter.check("5 rueee gusteav ze", **place_infos)
    assert not filter.check("5 rue gusteav zede", **place_infos)
    assert not filter.check("5 rue gusta zede", **place_infos)

    # Dashes are ignored
    assert filter.check("5 rue gustave--zede", **place_infos)

    # Bis/Ter/... are ignored in the query
    assert filter.check("5 Bis rue gustave zede", **place_infos)
    assert filter.check("5Ter rue gustave zede", **place_infos)

    # Support some abreviations
    assert filter.check("5 r gustave zédé", **place_infos)
    assert not filter.check("5 u gustave zédé", **place_infos)

    # Either names can match
    assert filter.check("5 zédéstraße", **place_infos)

    # Queries that match a small part of the request are ignored, postcode and
    # admins matter in relevant matching words.
    assert not filter.check(
        "101 dalmatiens", names=["101 rue des dalmatiens"], place_type="address"
    )

    assert filter.check(
        query="Paris 2e",
        names=["2e Arrondissement"],
        admins=["Paris"],
        postcodes=["75002"],
        place_type="admin",
    )


def test_rank():
    filter = ResultFilter()

    rennes = {
        "names": ["rue de Paris"],
        "admins": ["Rennes"],
        "place_type": "street",
    }

    paris = {
        "names": ["rue de Rennes"],
        "admins": ["Paris"],
        "place_type": "street",
    }

    assert filter.rank("rue de Rennes, Paris", **paris) > filter.rank(
        "rue de Rennes, Paris", **rennes
    )

    assert filter.rank("rue de Paris, Rennes", **rennes) > filter.rank(
        "rue de Paris, Rennes", **paris
    )


def test_match_word_prefix():
    filter = ResultFilter(match_word_prefix=True)

    place_infos = {
        "names": ["5 rue Gustave Zédé", "5, Zédéstraße"],
        "postcodes": ["79000"],
        "place_type": "house",
    }

    assert filter.check("5 rue Gust Zédé", **place_infos)


def test_min_matching_words():
    filter = ResultFilter(min_matching_words=3)

    place_infos = {
        "names": ["5 rue Gustave Zédé", "5, Zédéstraße"],
        "postcodes": ["79000"],
        "place_type": "house",
    }

    assert filter.check("5 rue Gustave Eiffel", **place_infos)
    assert not filter.check("5 rue Paul Dupont", **place_infos)


def test_match_postcode_by_prefix():
    filter = ResultFilter()
    place_infos = {
        "names": ["Niort"],
        "postcodes": ["79000"],
        "place_type": "admin",
    }
    assert filter.check("Niort 79", **place_infos)
    # At least 2 chars must match
    assert not filter.check("Niort 7", **place_infos)


def test_match_postcode_only():
    filter = ResultFilter()
    place_infos = {
        "names": ["Niort"],
        "postcodes": ["79000"],
        "place_type": "admin",
    }
    assert filter.check("79000", **place_infos)
    assert not filter.check("79", **place_infos)
