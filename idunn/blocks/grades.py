from apistar import validators

from .base import BaseBlock


class GradesBlock(BaseBlock):
    BLOCK_TYPE = "grades"

    total_grades_count = validators.Integer()
    global_grade = validators.Number()

    @classmethod
    def from_es(cls, es_poi, lang):
        raw_grades = es_poi.get_raw_grades() or {}
        total_grades_count = raw_grades.get('total_grades_count', None)
        global_grade = raw_grades.get('global_grade', None)

        if total_grades_count is None or global_grade is None:
            return None

        return cls(
            total_grades_count=total_grades_count,
            global_grade=global_grade,
        )
