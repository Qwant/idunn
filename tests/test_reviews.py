from unittest.mock import ANY

from idunn.blocks import ReviewsBlock
from idunn.places import TripadvisorPOI


def test_empty_review():
    reviews_block = ReviewsBlock.from_es(
        TripadvisorPOI(
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
                "administrative_regions": ANY,
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
                    "ta:url": "https://www.tripadvisor.com/Restaurant_Review-g190371-d14122469-Reviews-Cafe_Etagere-Vaduz.html?m=66562",
                    "poi_subclass": "sit_down",
                    "ta:photos_url": "https://www.tripadvisor.com/Restaurant_Review-g190371-d14122469-Reviews-Cafe_Etagere-Vaduz.html?m=66562#photos",
                    "ta:review_count": "0",
                    "phone": "+423 232 22 90",
                    "name": "Cafe Etagere",
                    "opening_hours": "Tu 08:30-18:30; We 08:30-18:30; Th 08:30-18:30; Fr 08:30-18:30; Sa 08:30-13:00",
                    "name:en": "Cafe Etagere",
                },
            },
            lang="de",
        ),
        lang="de",
    )

    assert reviews_block is None


def test_reviews_in_other_languages_with_priority_to_user_language_next_english_next_other_languages():
    reviews_block = ReviewsBlock.from_es(
        TripadvisorPOI(
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
                "administrative_regions": ANY,
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
                    "ta:reviews:0": '{"id":657030168,"DatePublished":"2019-03-07T14:42:06.000+0000","ReviewURL":"/ShowUserReviews-g190371-d14122469-r657030168-Cafe_Etagere-Vaduz.html?m=66562","MoreReviewsURL":"/Hotel_Review-g190364-d1866238-Reviews-Landhaus_Hotel_Restaurant-Nendeln.html?m=66562","Rating":4.0,"Language":"en","Title":"Good food","Text":"While here for work, this was one of two places I had dinner. Really good food, very fresh and the w...","TripType":"Business","Author":{"AuthorName":"Eddie N"}}',
                    "ta:reviews:1": '{"id":657030168,"DatePublished":"2020-04-07T14:42:06.000+0000","ReviewURL":"/ShowUserReviews-g190371-d14122469-r657030168-Cafe_Etagere-Vaduz.html?m=66562","MoreReviewsURL":"/Hotel_Review-g190364-d1866238-Reviews-Landhaus_Hotel_Restaurant-Nendeln.html?m=66562","Rating":4.0,"Language":"fr","Title":"L’albatros","Text":"L’albatros, oiseau immense avec des ailes de grande envergure, indolent compagnon de voyage, avec le...","TripType":"Business","Author":{"AuthorName":"Seb D"}}',
                    "ta:reviews:2": '{"id":657030168,"DatePublished":"2021-04-07T14:42:06.000+0000","ReviewURL":"/ShowUserReviews-g190371-d14122469-r657030168-Cafe_Etagere-Vaduz.html?m=66562","MoreReviewsURL":"/Hotel_Review-g190364-d1866238-Reviews-Landhaus_Hotel_Restaurant-Nendeln.html?m=66562","Rating":4.0,"Language":"de","Title":"Handwerklicher Bergbau","Text":"Das ist pure Geschichte an diese. etwas verlassenen Ort, der eigentlich nur der Durchfahrt dient. Ke..","TripType":"Business","Author":{"AuthorName":"Lukas S"}}',
                    "poi_subclass": "sit_down",
                    "ta:photos_url": "https://www.tripadvisor.com/Restaurant_Review-g190371-d14122469-Reviews-Cafe_Etagere-Vaduz.html?m=66562#photos",
                    "ta:review_count": "3",
                    "phone": "+423 232 22 90",
                    "name": "Cafe Etagere",
                    "opening_hours": "Tu 08:30-18:30; We 08:30-18:30; Th 08:30-18:30; Fr 08:30-18:30; Sa 08:30-13:00",
                    "name:en": "Cafe Etagere",
                },
            },
            lang="de",
        ),
        lang="de",
    )

    assert reviews_block.dict() == {
        "type": "reviews",
        "reviews": [
            {
                "date": "2021-04-07T14:42:06.000+0000",
                "rating": "4.0",
                "url": ANY,
                "more_reviews_url": ANY,
                "lang": "de",
                "title": "Handwerklicher Bergbau",
                "text": "Das ist pure Geschichte an diese. etwas verlassenen Ort, der eigentlich nur der Durchfahrt dient. Ke..",
                "trip_type": "Business",
                "author_name": "Lukas S",
            },
            {
                "date": "2019-03-07T14:42:06.000+0000",
                "rating": "4.0",
                "url": ANY,
                "more_reviews_url": ANY,
                "lang": "en",
                "title": "Good food",
                "text": "While here for work, this was one of two places I had dinner. Really good food, very fresh and the w...",
                "trip_type": "Business",
                "author_name": "Eddie N",
            },
            {
                "date": "2020-04-07T14:42:06.000+0000",
                "rating": "4.0",
                "url": ANY,
                "more_reviews_url": ANY,
                "lang": "fr",
                "title": "L’albatros",
                "text": "L’albatros, oiseau immense avec des ailes de grande envergure, indolent compagnon de voyage, avec le...",
                "trip_type": "Business",
                "author_name": "Seb D",
            },
        ],
    }


def test_sort_by_date_and_limit_to_3_reviews():
    reviews_block = ReviewsBlock.from_es(
        TripadvisorPOI(
            {
                "type": "poi",
                "id": "ta:poi:1700067",
                "label": "Schadler Ceramics Workshop",
                "name": "Schadler Ceramics Workshop",
                "coord": {"lon": 9.54484, "lat": 47.200242},
                "approx_coord": {"coordinates": [9.54484, 47.200242], "type": "Point"},
                "administrative_regions": ANY,
                "weight": 0.43227128489081945,
                "zip_codes": [],
                "poi_type": {
                    "id": "class_attraction:subclass_classes_&_workshops",
                    "name": "class_attraction subclass_classes_&_workshops",
                },
                "properties": {
                    "name": "Schadler Ceramics Workshop",
                    "name:de": "Keramik Werkstatt Schädler",
                    "name:en": "Schadler Ceramics Workshop",
                    "phone": "+423 373 14 20",
                    "poi_class": "attraction",
                    "poi_subclass": "classes_&_workshops",
                    "ta:average_rating": "5",
                    "ta:photos_url": "https://www.tripadvisor.com/Attraction_Review-g190364-d1700067-Reviews-Schadler_Ceramics_Workshop-Nendeln.html?m=66562#photos",
                    "ta:review_count": "4",
                    "ta:url": "https://www.tripadvisor.com/Attraction_Review-g190364-d1700067-Reviews-Schadler_Ceramics_Workshop-Nendeln.html?m=66562",
                    "image": "https://media-cdn.tripadvisor.com/media/photo-o/01/78/bd/84/keramik-werkstatt-schadler.jpg",
                    "ta:reviews:1": '{"id":385786013,"DatePublished":"2016-06-25T09:14:30.000+0000","ReviewURL":"/ShowUserReviews-g190364-d1700067-r385786013-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","MoreReviewsURL":"/Attraction_Review-g190364-d1700067-Reviews-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","Rating":5.0,"Language":"de","Title":"Keramik von Schaedler","Text":"Gratulation an Keramik von Schaedler, Gratulation an den Nachwuchs: ein Auszubildender hat am Sommer...","TripType":null,"Author":{"AuthorName":"Markus S"}}',
                    "ta:reviews:0": '{"id":572766410,"DatePublished":"2018-04-11T22:14:04.000+0000","ReviewURL":"/ShowUserReviews-g190364-d1700067-r572766410-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","MoreReviewsURL":"/Attraction_Review-g190364-d1700067-Reviews-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","Rating":5.0,"Language":"de","Title":"Kleinod","Text":"Das ist pure Geschichte an diese. etwas verlassenen Ort, der eigentlich nur der Durchfahrt dient. Ke...","TripType":null,"Author":{"AuthorName":"74markusb"}}',
                    "ta:reviews:3": '{"id":138540991,"DatePublished":"2012-08-27T10:58:48.000+0000","ReviewURL":"/ShowUserReviews-g190364-d1700067-r138540991-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","MoreReviewsURL":"/Attraction_Review-g190364-d1700067-Reviews-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","Rating":4.0,"Language":"en","Title":"nice ceramics","Text":"Come here to buy some pieces every time i visit Liechtenstein. Handcrafted ceramics you dont find el...","TripType":"Family","Author":{"AuthorName":"Sigrid66"}}',
                    "ta:reviews:2": '{"id":760466838,"DatePublished":"2020-07-18T04:23:27.000+0000","ReviewURL":"/ShowUserReviews-g190364-d1700067-r760466838-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","MoreReviewsURL":"/Attraction_Review-g190364-d1700067-Reviews-Schadler_Ceramics_Workshop-Nendeln.html?m=66562","Rating":5.0,"Language":"en","Title":"Super ceramics","Text":"Made a quick visit here on my whistle stop tour of Liechtenstein and was very impressed with the sim...","TripType":"Solo","Author":{"AuthorName":"jennymul"}}',
                },
                "address": {
                    "type": "street",
                    "id": "",
                    "name": "",
                    "administrative_regions": [],
                    "label": "Churer Strasse 3, Nendeln 9485 Liechtenstein",
                    "weight": 0.0,
                    "approx_coord": None,
                    "coord": {"lon": 9.54484, "lat": 47.200242},
                    "zip_codes": [],
                    "country_codes": [],
                    "context": None,
                },
                "country_codes": ["LI", "LI"],
                "names": {"de": "Keramik Werkstatt Schädler", "en": "Schadler Ceramics Workshop"},
                "labels": {"de": "Keramik Werkstatt Schädler", "en": "Schadler Ceramics Workshop"},
                "context": None,
            },
            lang="de",
        ),
        lang="de",
    )

    assert reviews_block.dict() == {
        "type": "reviews",
        "reviews": [
            {
                "date": "2018-04-11T22:14:04.000+0000",
                "rating": ANY,
                "url": ANY,
                "more_reviews_url": ANY,
                "lang": "de",
                "title": ANY,
                "text": ANY,
                "trip_type": ANY,
                "author_name": "74markusb",
            },
            {
                "date": "2016-06-25T09:14:30.000+0000",
                "rating": ANY,
                "url": ANY,
                "more_reviews_url": ANY,
                "lang": "de",
                "title": ANY,
                "text": ANY,
                "trip_type": ANY,
                "author_name": "Markus S",
            },
            {
                "date": "2020-07-18T04:23:27.000+0000",
                "rating": ANY,
                "url": ANY,
                "more_reviews_url": ANY,
                "lang": "en",
                "title": ANY,
                "text": ANY,
                "trip_type": ANY,
                "author_name": "jennymul",
            },
        ],
    }
