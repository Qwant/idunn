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
    "idunn_exceptions_count",
    "Number of exceptions caught in Idunn.",
    ["exception_type"]
)

IDUNN_WIKI_BREAKER_ERRORS_COUNT = Counter(
    "idunn_breaker_errors_count",
    "Number of errors caught by the breaker.",
    []
)

IDUNN_WIKI_RATE_LIMITER_MAX_COUNT = Counter(
    "idunn_limiter_too_many_requests_count",
    "Number of times TooManyRequests exception has been raised.",
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

def limiter_exception():
    IDUNN_WIKI_RATE_LIMITER_MAX_COUNT.inc()
