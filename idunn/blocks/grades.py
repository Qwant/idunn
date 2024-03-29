from .base import BaseBlock
from typing import Optional, Literal


class GradesBlock(BaseBlock):
    type: Literal["grades"] = "grades"
    total_grades_count: int
    global_grade: float
    url: Optional[str]

    @classmethod
    def from_es(cls, place, lang):
        raw_grades = place.get_raw_grades() or {}
        total_grades_count = raw_grades.get("total_grades_count", None)
        global_grade = raw_grades.get("global_grade", None)
        if total_grades_count is None or global_grade is None:
            return None

        return cls(
            total_grades_count=total_grades_count,
            global_grade=global_grade,
            url=place.get_reviews_url() or None,
        )
