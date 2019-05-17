from apistar import validators

from .base import BaseBlock


class OpeningDayEvent(BaseBlock):
    BLOCK_TYPE = "event_opening_date"

    date_start = validators.String()
    date_end = validators.String()
    space_time_info = validators.String(allow_null=True)
    timetable = validators.Array(allow_null=True)

    @classmethod
    def from_es(cls, es_poi, lang):
        date_start = es_poi.get('date_start')
        date_end = es_poi.get('date_end')
        space_time_info= es_poi.get('space_time_info', None)
        timetable = es_poi.get('timetable', None)

        if isinstance(timetable, str):
            timetable = timetable.split(';')

        if not (date_start or date_end or space_time_info or timetable):
            return None

        return cls(
            date_start=date_start,
            date_end=date_end,
            space_time_info=space_time_info,
            timetable=timetable
        )


class DescriptionEvent(BaseBlock):
    BLOCK_TYPE = "event_description"

    description = validators.String(allow_null=True)
    free_text = validators.String(allow_null=True)
    price = validators.String(allow_null=True)

    @classmethod
    def from_es(cls, es_poi, lang):
        description = es_poi.get('description', None)
        free_text =  es_poi.get('free_text', None)
        price = es_poi.get('price', None)

        if not (description or free_text or price):
            return None

        return cls(
            description=description,
            free_text=free_text,
            price=price
        )




