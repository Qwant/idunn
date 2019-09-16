from apistar import validators, types

from .base import BaseBlock


class TimeTableItem(types.Type):
    beginning = validators.DateTime()
    end = validators.DateTime()


class OpeningDayEvent(BaseBlock):
    BLOCK_TYPE = "event_opening_dates"

    date_start = validators.DateTime()
    date_end = validators.DateTime()
    space_time_info = validators.String(allow_null=True)
    timetable = validators.Array(items=TimeTableItem)

    @classmethod
    def from_es(cls, es_poi, lang):
        if es_poi.PLACE_TYPE != 'event':
            return None

        date_start = es_poi.get('date_start')
        date_end = es_poi.get('date_end')
        space_time_info= es_poi.get('space_time_info')
        timetable = es_poi.get('timetable') or ''

        if not date_start or not date_end:
            return None

        timetable = timetable.split(';')
        new_format_timetable = []
        for tt in filter(None, timetable):
            date_start_end = tt.split(' ')
            new_format_timetable.append(
                TimeTableItem(beginning=date_start_end[0], end=date_start_end[1])
            )

        timetable = new_format_timetable

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
    tags = validators.Array(allow_null=True)

    @classmethod
    def from_es(cls, es_poi, lang):
        if es_poi.PLACE_TYPE != 'event':
            return None

        description = es_poi.get('description')
        free_text =  es_poi.get('free_text')
        price = es_poi.get('pricing_info')
        tags = es_poi.get('tags', [])

        if isinstance(tags, str):
            tags = tags.split(';')

        if not description:
            return None

        return cls(
            description=description,
            free_text=free_text,
            price=price,
            tags=tags
        )
