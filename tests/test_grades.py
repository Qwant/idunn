from idunn.blocks.grades import GradesBlock
from idunn.places import POI

def test_grades_block():
    web_block = GradesBlock.from_es(
        POI({
            "properties": {
                "grades": {
                    "total_grades_count": 8,
                    "global_grade": 4,
                }
            }
        }),
        lang='en'
    )

    assert web_block == GradesBlock(
        total_grades_count=8,
        global_grade=4.
    )
