from .base import BaseBlock
from pydantic import BaseModel
from datetime import datetime
from typing import ClassVar, List, Literal, Optional


class TimeTableItem(BaseModel):
    beginning: datetime
    end: datetime


class OpeningDayEvent(BaseBlock):
    type: Literal["event_opening_dates"] = "event_opening_dates"
    date_start: datetime
    date_end: datetime
    space_time_info: Optional[str]
    timetable: List[TimeTableItem]

    @classmethod
    def from_es(cls, es_poi, lang):
        if es_poi.PLACE_TYPE != "event":
            return None

        date_start = es_poi.get("date_start")
        date_end = es_poi.get("date_end")
        space_time_info = es_poi.get("space_time_info")
        timetable = es_poi.get("timetable") or ""

        if not date_start or not date_end:
            return None

        timetable = timetable.split(";")
        new_format_timetable = []
        for tt in filter(None, timetable):
            date_start_end = tt.split(" ")
            new_format_timetable.append(
                TimeTableItem(beginning=date_start_end[0], end=date_start_end[1])
            )

        timetable = new_format_timetable

        return cls(
            date_start=date_start,
            date_end=date_end,
            space_time_info=space_time_info,
            timetable=timetable,
        )


class DescriptionEvent(BaseBlock):
    type: Literal["event_description"] = "event_description"
    description: Optional[str]
    free_text: Optional[str]
    price: Optional[str]
    tags: List[str]

    @classmethod
    def from_es(cls, es_poi, lang):
        if es_poi.PLACE_TYPE != "event":
            return None

        description = es_poi.get("description")
        free_text = es_poi.get("free_text")
        price = es_poi.get("pricing_info")
        tags = es_poi.get("tags", [])

        if isinstance(tags, str):
            tags = tags.split(";")

        if not description:
            return None

        return cls(description=description, free_text=free_text, price=price, tags=tags)
