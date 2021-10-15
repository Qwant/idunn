from idunn.blocks.grades import GradesBlock
from idunn.places import PjApiPOI
from idunn.places.models import pj_info


def test_grades_block():
    grades_block = GradesBlock.from_es(
        PjApiPOI(
            pj_info.Response(
                **{
                    "inscriptions": [
                        {
                            "reviews": {"total_reviews": 8, "overall_review_rating": 4},
                            "address_district": "03",
                            "address_street": "5 r Thorigny",
                            "address_zipcode": "75003",
                        }
                    ]
                }
            )
        ),
        lang="en",
    )

    assert grades_block == GradesBlock(
        total_grades_count=8,
        global_grade=4.0,
        url="https://www.pagesjaunes.fr/pros/None#ancreBlocAvis",
    )
