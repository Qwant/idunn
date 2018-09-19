import time

from apistar import Component
from prometheus_client import Counter, Gauge, Histogram


WIKI_REQUEST_DURATION = Histogram(
    "wiki_request_duration_seconds",
    "Time spent processing a Wiki request.",
    ["handler"],
)

WIKI_BREAKER_STATUS = Gauge(
    "breaker_status",
    "Breaker status, open (=2) or half-open (=1) or close (=0).",
    []
)

WIKI_BREAKER_EXCEPTIONS_COUNT = Counter(
    "breaker_exceptions_count",
    "Number of exceptions caught by the breaker.",
    []
)

WIKI_RATE_LIMITER_MAX_COUNT = Counter(
    "limiter_too_many_requests_count",
    "Number of times TooManyRequests exception has been raised.",
    []
)

BREAKER_STATUS = {'closed': 0, 'half-open':1, 'open': 2}

class PrometheusTracker:
    """ The logic of the Prometheus metrics is defined in this component """

    _tracker = None

    class _Prometheus:
        """ Singleton that catch some primitives on the Prometheus metrics """

        def request_start(self, handler):
            self.start_time = time.monotonic()

        def request_end(self, handler):
            start_time = getattr(self, "start_time", None)
            if start_time is not None:
                duration = time.monotonic() - start_time
                WIKI_REQUEST_DURATION.labels(handler).observe(duration)

        def breaker_exception(self):
            WIKI_BREAKER_EXCEPTIONS_COUNT.inc()

        def limiter_exception(self):
            WIKI_RATE_LIMITER_MAX_COUNT.inc()

        def update_status(self, old_status, new_status):
            diff = BREAKER_STATUS.get(old_status) - BREAKER_STATUS.get(new_status)
            if (lambda x: (1, -1)[x < 0])(diff) == 1:
                for i in range(0, diff):
                    WIKI_BREAKER_STATUS.inc()
            else:
                for i in range(0, abs(diff)):
                    WIKI_BREAKER_STATUS.dec()

    @classmethod
    def get_tracker(cls):
        if cls._tracker is None:
            cls._tracker = cls._Prometheus()
        return cls._tracker
