import contextlib
import time

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import Response

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess


""" The logic of the Prometheus metrics is defined in this module """


IDUNN_WIKI_REQUEST_DURATION = Histogram(
    "idunn_wiki_request_duration_seconds",
    "Time spent processing a Wiki request.",
    ["target", "handler"],
)

IDUNN_WIKI_EXCEPTIONS_COUNT = Counter(
    "idunn_wiki_exceptions_count",
    "Number of exceptions caught in Idunn WikipediaBlock.",
    ["exception_type"]
)


@contextlib.contextmanager
def wiki_request_duration(target, handler):
    with IDUNN_WIKI_REQUEST_DURATION.labels(target, handler).time():
        yield

def exception(exception_type):
    IDUNN_WIKI_EXCEPTIONS_COUNT.labels(exception_type).inc()


# code from apistar_prometheus
_HEADERS = {"content-type": CONTENT_TYPE_LATEST}


def expose_metrics():
    return Response(generate_latest(), headers=_HEADERS)


def expose_metrics_multiprocess():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), headers=_HEADERS)


REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Time spent processing a request.",
    ["method", "handler"],
)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Request count by method, handler and response code.",
    ["method", "handler", "code"],
)
REQUESTS_INPROGRESS = Gauge(
    "http_requests_inprogress",
    "Requests in progress by method and handler",
    ["method", "handler"],
)


class Prometheus:
    def track_request_start(self, method, handler=None):
        self.start_time = time.monotonic()

        handler_name = "<builtin>"
        if handler is not None:
            handler_name = "%s.%s" % (handler.__module__, handler.__name__)

        REQUESTS_INPROGRESS.labels(method, handler_name).inc()

    def track_request_end(self, method, handler, status_code):
        handler_name = "<builtin>"
        if handler is not None:
            handler_name = "%s.%s" % (handler.__module__, handler.__name__)

        start_time = getattr(self, "start_time", None)
        if start_time is not None:
            duration = time.monotonic() - start_time
            REQUEST_DURATION.labels(method, handler_name).observe(duration)

        REQUEST_COUNT.labels(method, handler_name, status_code).inc()
        REQUESTS_INPROGRESS.labels(method, handler_name).dec()
