import time
import contextlib

from apistar import Component
from prometheus_client import Counter, Gauge, Histogram


""" The logic of the Prometheus metrics is defined in this module """


IDUNN_WIKI_REQUEST_DURATION = Histogram(
    "idunn_wiki_request_duration_seconds",
    "Time spent processing a Wiki request.",
    ["target", "handler"],
)

IDUNN_WIKI_EXCEPTIONS_COUNT = Counter(
    "idunn_wiki_exceptions_count",
    "Number of exceptions caught in Idunn.",
    ["exception_type"]
)

IDUNN_WIKI_BREAKER_ERRORS_COUNT = Counter(
    "idunn_breaker_errors_count",
    "Number of errors caught by the breaker.",
    []
)


@contextlib.contextmanager
def wiki_request_duration(target, handler):
    with IDUNN_WIKI_REQUEST_DURATION.labels(target, handler).time():
        yield

def breaker_error():
    IDUNN_WIKI_BREAKER_ERRORS_COUNT.inc()

def exception(exception_type):
    IDUNN_WIKI_EXCEPTIONS_COUNT.labels(exception_type).inc()
