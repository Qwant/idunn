import humanized_opening_hours as hoh
from humanized_opening_hours.field_parser import WEEKDAYS, YearTransformer

"""
This is an ugly patch to work around a bug that caused
an infinite loop when a day range overlaps the end of the week.
eg: We-Mo

This will be fixed in the next release of humanized_opening_hours,
still in alpha to this day (2018-07-09)
"""
def patched_raw_consecutive_day_range(self, args):
    """ Original implementation:
    https://github.com/rezemika/humanized_opening_hours/blob/v0.6.2/humanized_opening_hours/field_parser.py#L70
    """
    first_day = WEEKDAYS.index(args[0])
    last_day = WEEKDAYS.index(args[1])
    if first_day <= last_day:
        day_indexes = range(first_day, last_day+1)
    else:
        day_indexes = (i%7 for i in range(first_day, last_day+1+7))
    return set(WEEKDAYS[i] for i in day_indexes)

YearTransformer.raw_consecutive_day_range = patched_raw_consecutive_day_range
hoh.field_parser.PARSER = hoh.field_parser.get_parser()
