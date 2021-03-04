from idunn.utils.result_filter import check, rank


def test_filter():
    place_infos = {
        "names": ["5 rue Gustave Zédé", "5, Zédéstraße"],
        "postcodes": ["79000"],
        "place_type": "address",
    }

    # Case is ignored
    assert check("5 RuE gustave ZÉDÉ", **place_infos)

    # Extra terms are not allowed
    assert not check("5 rue gustave zédé restaurant", **place_infos)

    # Numbers must match
    assert not check("1 rue gustave zédé", **place_infos)
    assert not check("5 rue gustave zédé 75015", **place_infos)

    # Accents can be omitted
    assert check("5 rue gustave zede", **place_infos)

    # Accents in the request still matter
    assert not check("5 rue güstâve zédé", **place_infos)

    # A single spelling mistake is allowed per word
    assert check("5 ruee gustaev zde", **place_infos)
    assert not check("5 rueee gusteav ze", **place_infos)
    assert not check("5 rue gusteav zede", **place_infos)
    assert not check("5 rue gusta zede", **place_infos)

    # Dashes are ignored
    assert check("5 rue gustave--zede", **place_infos)

    # Bis/Ter/... are ignored in the query
    assert check("5 Bis rue gustave zede", **place_infos)
    assert check("5Ter rue gustave zede", **place_infos)

    # Support some abreviations
    assert check("5 r gustave zédé", **place_infos)
    assert not check("5 u gustave zédé", **place_infos)

    # Either names can match
    assert check("5 zédéstraße", **place_infos)

    # Queries that match a small part of the request are ignored, postcode and
    # admins matter in relevant matching words.
    assert not check("101 dalmatiens", names=["101 rue des dalmatiens"], place_type="address")
    assert check(
        query="Paris 2e",
        names=["2e Arrondissement"],
        admins=["Paris"],
        postcodes=["75002"],
        place_type="admin",
    )


def test_rank():
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

    assert rank("rue de Rennes, Paris", **paris) > rank("rue de Rennes, Paris", **rennes)
    assert rank("rue de Paris, Rennes", **rennes) > rank("rue de Paris, Rennes", **paris)
