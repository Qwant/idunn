import re
from pathlib import Path

patterns_path = Path(__file__).with_name("patterns_to_ignore.txt")
with open(patterns_path) as file:
    patterns = [p for line in file if (p := line.strip())]
    ignore_pattern_start = re.compile(rf'^({"|".join(patterns)})( +|$)')
    ignore_pattern_end = re.compile(rf' +({"|".join(patterns)})$')


def normalize(query):
    query = query.strip().lower()
    query = ignore_pattern_start.sub("", query)
    query = ignore_pattern_end.sub("", query)
    return query
