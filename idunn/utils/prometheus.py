import time
import contextlib

from apistar import Component
from prometheus_client import Counter, Gauge, Histogram


""" The logic of the Prometheus metrics is defined in this module """


IDUNN_WIKI_REQUEST_DURATION = Histogram(
    "idunn_wiki_request_duration_seconds",
    "Time spent processing a Wiki request.",
    ["handler"],
)

IDUNN_WIKI_BREAKER_EXCEPTIONS_COUNT = Counter(
    "idunn_breaker_exceptions_count",
    "Number of exceptions caught by the breaker.",
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

class PrometheusTracker:
    """ Just catch some primitives on the Prometheus metrics """

    @contextlib.contextmanager
    def log_request_duration(self, handler):
        with IDUNN_WIKI_REQUEST_DURATION.labels(handler).time():
            yield

    def breaker_error(self):
        IDUNN_WIKI_BREAKER_ERRORS_COUNT.inc()

    def breaker_exception(self, exception_type):
        IDUNN_WIKI_BREAKER_EXCEPTIONS_COUNT.labels(exception_type).inc()

    def limiter_exception(self):
        IDUNN_WIKI_RATE_LIMITER_MAX_COUNT.inc()
