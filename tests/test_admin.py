from idunn.places.admin import Admin


def test_admin():
    admin = Admin(
        {
            "zone_type": "city",
            "codes": [{"name": "wikidata", "value": "Q7652"}],
            "names": {
                "de": "Dünkirchen",
                "en": "Dunkirk",
                "es": "Dunkerque",
                "fr": "Dunkerque",
                "it": "Dunkerque",
            },
            "labels": {
                "br": "Dunkerque (59140-59640), Norzh-Pas-de-Calais, Krec'hioù-Frañs, Bro-C'hall",
                "ca": "Dunkerque (59140-59640), Nord, Alts de França, França",
                "de": "Dünkirchen (59140-59640), Nord, Nordfrankreich, Frankreich",
                "en": "Dunkirk (59140-59640), Nord, Nord-Pas-de-Calais and Picardy, France",
                "es": "Dunkerque (59140-59640), Norte, Alta Francia, Francia",
                "it": "Dunkerque (59140-59640), Nord, Nord-Passo di Calais e Piccardia, Francia",
            },
        }
    )

    assert admin.get_name("fr") == "Dunkerque"
    assert admin.get_name("da") == ""
    assert admin.wikidata_id == "Q7652"


def test_admin_bbox_override():
    admin = Admin(
        {
            "zone_type": "city",
            "codes": [{"name": "wikidata", "value": "Q142"}],
            "names": {
                "fr": "France",
            },
            "labels": {
                "fr": "France",
            },
        }
    )

    assert admin.wikidata_id == "Q142"
    assert admin.get_bbox() == [-5.4517733, 41.2611155, 9.8282225, 51.3055721]
