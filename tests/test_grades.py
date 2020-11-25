from idunn.blocks.grades import GradesBlock
from idunn.places import LegacyPjPOI


def test_grades_block():
    web_block = GradesBlock.from_es(
        LegacyPjPOI({"grades": {"total_grades_count": 8, "global_grade": 4,}}), lang="en"
    )

    assert web_block == GradesBlock(total_grades_count=8, global_grade=4.0, url=None)
