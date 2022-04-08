from idunn.blocks import ReviewsBlock
from idunn.blocks.grades import GradesBlock
from idunn.places import PjApiPOI
from idunn.places.models import pj_info


def test_reviews_block():
    reviews_block = ReviewsBlock.from_es(
        {
            "address": {
                "administrative_regions": [],
                "coord": {"lon": 9.52061, "lat": 47.14165},
                "name": "",
                "context": None,
                "weight": 0.0,
                "country_codes": [],
                "approx_coord": None,
                "id": "",
                "label": "Herrengasse 8, Vaduz 9490 Liechtenstein",
                "type": "street",
                "zip_codes": [],
            },
            "weight": 0.34557291336697865,
            "label": "Cafe Etagere",
            "type": "poi",
            "labels": {"en": "Cafe Etagere"},
            "administrative_regions": [
                {
                    "codes": {"ISO3166-2": "LI-11", "wikidata": "Q1844"},
                    "level": 8,
                    "bbox": [9.4950763, 47.0870567, 9.6116778, 47.1940393],
                    "weight": 0.0,
                    "label": "Vaduz, Oberland, Liechtenstein",
                    "type": "admin",
                    "labels": {},
                    "administrative_regions": [],
                    "coord": {"lon": 9.54522741314287, "lat": 47.13894943693524},
                    "names": {"it": "Vaduz"},
                    "insee": "",
                    "parent_id": "admin:osm:relation:1156142",
                    "name": "Vaduz",
                    "context": None,
                    "country_codes": [],
                    "approx_coord": None,
                    "zone_type": "city",
                    "id": "admin:osm:relation:1155956",
                    "zip_codes": [],
                },
                {
                    "codes": {"wikidata": "Q25619881"},
                    "level": 6,
                    "bbox": [9.4716736, 47.0484291, 9.6357143, 47.194226699999994],
                    "weight": 0.0,
                    "label": "Oberland, Liechtenstein",
                    "type": "admin",
                    "labels": {},
                    "administrative_regions": [],
                    "coord": {"lon": 9.55725569885172, "lat": 47.119539507602},
                    "names": {},
                    "insee": "",
                    "parent_id": "admin:osm:relation:1155955",
                    "name": "Oberland",
                    "context": None,
                    "country_codes": [],
                    "approx_coord": None,
                    "zone_type": "state",
                    "id": "admin:osm:relation:1156142",
                    "zip_codes": [],
                },
                {
                    "codes": {"wikidata": "Q25619881"},
                    "level": 6,
                    "bbox": [9.4716736, 47.0484291, 9.6357143, 47.194226699999994],
                    "weight": 0.0,
                    "label": "Oberland, Liechtenstein",
                    "type": "admin",
                    "labels": {"be": "Oberland, Лiхтэнштэйн"},
                    "administrative_regions": [],
                    "coord": {"lon": 9.557255655389657, "lat": 47.11953947335839},
                    "names": {},
                    "insee": "",
                    "parent_id": "admin:osm:relation:1155955",
                    "name": "Oberland",
                    "context": None,
                    "country_codes": [],
                    "approx_coord": None,
                    "zone_type": "state",
                    "id": "admin:osm:relation:1156142",
                    "zip_codes": [],
                },
                {
                    "codes": {
                        "ISO3166-1:alpha3": "LIE",
                        "ISO3166-1": "LI",
                        "ISO3166-1:alpha2": "LI",
                        "wikidata": "Q347",
                        "ISO3166-1:numeric": "438",
                    },
                    "level": 2,
                    "bbox": [9.4716736, 47.0484291, 9.6357143, 47.270581],
                    "weight": 2.7965e-05,
                    "label": "Liechtenstein",
                    "type": "admin",
                    "labels": {},
                    "administrative_regions": [],
                    "coord": {"lon": 9.5227962, "lat": 47.1392862},
                    "names": {
                        "de": "Liechtenstein",
                        "en": "Liechtenstein",
                        "it": "Liechtenstein",
                        "fr": "Liechtenstein",
                        "es": "Liechtenstein",
                    },
                    "insee": "",
                    "parent_id": None,
                    "name": "Liechtenstein",
                    "context": None,
                    "country_codes": ["LI"],
                    "approx_coord": None,
                    "zone_type": "country",
                    "id": "admin:osm:relation:1155955",
                    "zip_codes": [],
                },
                {
                    "codes": {
                        "ISO3166-1:alpha3": "LIE",
                        "ISO3166-1": "LI",
                        "ISO3166-1:alpha2": "LI",
                        "wikidata": "Q347",
                        "ISO3166-1:numeric": "438",
                    },
                    "level": 2,
                    "bbox": [9.4716736, 47.0484291, 9.6357143, 47.270581],
                    "weight": 2.7965e-05,
                    "label": "Liechtenstein",
                    "type": "admin",
                    "labels": {"be": "Лiхтэнштэйн"},
                    "administrative_regions": [],
                    "coord": {"lon": 9.5227962, "lat": 47.1392862},
                    "names": {
                        "de": "Liechtenstein",
                        "be": "Лiхтэнштэйн",
                        "en": "Liechtenstein",
                        "it": "Liechtenstein",
                        "fr": "Liechtenstein",
                        "es": "Liechtenstein",
                    },
                    "insee": "",
                    "parent_id": None,
                    "name": "Liechtenstein",
                    "context": None,
                    "country_codes": ["LI"],
                    "approx_coord": None,
                    "zone_type": "country",
                    "id": "admin:osm:relation:1155955",
                    "zip_codes": [],
                },
            ],
            "coord": {"lon": 9.52061, "lat": 47.14165},
            "names": {"en": "Cafe Etagere"},
            "name": "Cafe Etagere",
            "context": None,
            "country_codes": ["LI", "LI"],
            "approx_coord": {"coordinates": [9.52061, 47.14165], "type": "Point"},
            "poi_type": {
                "name": "class_restaurant subclass_sit_down",
                "id": "class_restaurant:subclass_sit_down",
            },
            "id": "ta:poi:14122469",
            "zip_codes": [],
            "properties": {
                "poi_class": "restaurant",
                "image": "https://media-cdn.tripadvisor.com/media/photo-s/15/87/5e/b3/das-cafe-etagere-befindet.jpg",
                "website": "https://www.facebook.com/cafeetagere/",
                "ta:average_rating": "4",
                "ta:url": "https://www.tripadvisor.com/Restaurant_Review-g190371-d14122469-Reviews-Cafe_Etagere-Vaduz.html?m=66562",
                "ta:reviews:0": '{"id":657030168,"DatePublished":"2019-03-07T14:42:06.000+0000","ReviewURL":"/ShowUserReviews-g190371-d14122469-r657030168-Cafe_Etagere-Vaduz.html?m=66562","Language":"en","Title":"Good food","Text":"While here for work, this was one of two places I had dinner. Really good food, very fresh and the w...","TripType":"Business","Author":{"AuthorName":"Eddie N"}}',
                "poi_subclass": "sit_down",
                "ta:photos_url": "https://www.tripadvisor.com/Restaurant_Review-g190371-d14122469-Reviews-Cafe_Etagere-Vaduz.html?m=66562#photos",
                "ta:review_count": "1",
                "phone": "+423 232 22 90",
                "name": "Cafe Etagere",
                "opening_hours": "Tu 08:30-18:30; We 08:30-18:30; Th 08:30-18:30; Fr 08:30-18:30; Sa 08:30-13:00",
                "name:en": "Cafe Etagere",
            },
        },
        lang="de",
    )

    assert reviews_block == ReviewsBlock(
        date="2019-03-07T14:42:06.000+0000",
        url="https://www.tripadvisor.com/Restaurant_Review-g190371-d14122469-Reviews-Cafe_Etagere-Vaduz.html?m=66562/ShowUserReviews-g190371-d14122469-r657030168-Cafe_Etagere-Vaduz.html?m=66562",
        lang="en",
        title="Good food",
        text="While here for work, this was one of two places I had dinner. Really good food, very fresh and the w...",
        trip_type="Business",
        author_name="Eddie N",
    )