from idunn.blocks.grades import GradesBlock
from idunn.places import PjPOI


def test_grades_block():
    grades_block = GradesBlock.from_es(
        PjPOI(
            {
                "grades": {
                    "total_grades_count": 8,
                    "global_grade": 4,
                }
            }
        ),
        lang="en",
    )

    assert grades_block == GradesBlock(total_grades_count=8, global_grade=4.0, url=None)
