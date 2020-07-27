import os
from datetime import date, datetime, time, timedelta

from pytz import utc
from py_mini_racer.py_mini_racer import MiniRacer

DIR = os.path.dirname(__file__)
OPENING_HOURS_JS = os.path.join(DIR, "data/opening_hours.min.js")
OPENING_HOURS_JS_WRAPPER = os.path.join(DIR, "data/opening_hours_wrapper.js")


class OpeningHoursEngine:
    def __init__(self):
        with open(OPENING_HOURS_JS, "r") as f:
            js_sources = f.read()

        with open(OPENING_HOURS_JS_WRAPPER, "r") as f:
            js_wrapper = f.read()

        self.js_ctx = MiniRacer()
        self.js_ctx.eval(js_sources)
        self.js_ctx.eval(js_wrapper)

    def call(self, *args, **kwargs):
        return self.js_ctx.call(*args, **kwargs)


engine = OpeningHoursEngine()


class OpeningHours:
    def __init__(self, oh, tz, country_code):
        if country_code is not None:
            country_code = country_code.lower()

        self.raw = oh
        self.tz = tz
        self.nmt_obj = {"address": {"country_code": country_code}}

    def validate(self):
        """Check if an expression parses correctly"""
        return engine.call("validate", self.raw, self.nmt_obj) is True

    def is_24_7(self, dt):
        """Check if this is always open starting from a given date"""
        assert isinstance(dt, datetime)
        return self.is_open(dt) and self.next_change(dt) is None

    def is_open(self, dt):
        """Check if open at a given time"""
        assert isinstance(dt, datetime)
        return engine.call("wrapIsOpen", self.raw, self.nmt_obj, dt.astimezone(self.tz).isoformat())

    def is_open_at_date(self, d):
        """Check if this is open at some point in a given date"""
        assert isinstance(d, date)
        start = datetime.combine(d, time(0, 0))
        end = datetime.combine(d + timedelta(days=1), time(0, 0))
        return bool(self.get_open_intervals(start, end))

    def next_change(self, dt):
        """Get datetime of next change of state"""
        assert isinstance(dt, datetime)
        date = engine.call(
            "wrapNextChange", self.raw, self.nmt_obj, dt.astimezone(self.tz).isoformat()
        )

        if date is None:
            return None

        return self.tz.localize(datetime.fromisoformat(date))

    def get_open_intervals(self, start, end):
        """Get opened intervals for a period of time"""
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        return [
            (
                self.tz.localize(datetime.fromisoformat(start)),
                self.tz.localize(datetime.fromisoformat(end)),
                unknown,
                comment,
            )
            for [start, end, unknown, comment] in engine.call(
                "wrapOpenIntervals",
                self.raw,
                self.nmt_obj,
                start.astimezone(self.tz).isoformat(),
                end.astimezone(self.tz).isoformat(),
            )
        ]

    def get_open_intervals_at_date(self, d, overlap_next_day=False):
        """
        Get opening intervals at given date. By default the intervals will be
        included in the day (00:00 -> 24:00), if overlap_next_day is set,
        intervals will be assigned without being truncated to the day they
        start in.
        """
        assert isinstance(d, date)
        start = self.tz.localize(datetime.combine(d, time(0, 0)))
        end = self.tz.localize(datetime.combine(d + timedelta(1), time(0, 0)))

        def map_interval(interval):
            rg_start, rg_end, unknown, comment = interval

            # Keep only intervals that overlap with input day
            if rg_end <= start or rg_start >= end:
                return None

            # We constraint the interval in current day in either of these cases:
            #   1. overlap is disabled
            #   2. the interval is longer than a full day (otherwise it would raise weird cases)
            if not overlap_next_day or rg_end - rg_start > timedelta(days=1):
                rg_start = max(rg_start, start)
                rg_end = min(rg_end, end)

            # With overlap enabled, keep only intervals that start today
            # (others would be considered as belonging to previous day)
            if overlap_next_day and not start <= rg_start < end:
                return None

            # Check the interval is not empty
            if rg_end < rg_start:
                return None

            return (rg_start, rg_end, unknown, comment)

        # Query open intervals for previous and next day and use previously defined filter
        intervals = self.get_open_intervals(start - timedelta(days=1), end + timedelta(days=1))
        return list(filter(None, map(map_interval, intervals)))
