import contextlib
import time

from starlette.responses import Response
from starlette.requests import Request

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)

from fastapi.routing import APIRoute
from starlette.responses import PlainTextResponse


""" The logic of the Prometheus metrics is defined in this module """


IDUNN_WIKI_REQUEST_DURATION = Histogram(
    "idunn_wiki_request_duration_seconds",
    "Time spent processing a Wiki request.",
    ["target", "handler"],
)

IDUNN_EXCEPTIONS_COUNT = Counter(
    "idunn_exceptions_count", "Number of exceptions caught in Idunn", ["exception_type"]
)


@contextlib.contextmanager
def wiki_request_duration(target, handler):
    with IDUNN_WIKI_REQUEST_DURATION.labels(target, handler).time():
        yield


def exception(exception_type):
    IDUNN_EXCEPTIONS_COUNT.labels(exception_type).inc()


# code from apistar_prometheus
_HEADERS = {"content-type": CONTENT_TYPE_LATEST}


def expose_metrics():
    return Response(generate_latest(), headers=_HEADERS)


def expose_metrics_multiprocess():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), headers=_HEADERS)


REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "Time spent processing a request.", ["method", "handler"],
)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Request count by method, handler and response code.",
    ["method", "handler", "code"],
)
REQUESTS_INPROGRESS = Gauge(
    "http_requests_inprogress", "Requests in progress by method and handler", ["method", "handler"],
)


class MonitoredAPIRoute(APIRoute):
    def get_route_handler(self):
        handler_name = self.name
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            method = request["method"]
            REQUESTS_INPROGRESS.labels(method=method, handler=handler_name).inc()
            try:
                before_time = time.monotonic()
                response = await original_handler(request)
                after_time = time.monotonic()
            except Exception as e:
                raise e from None
            else:
                REQUEST_DURATION.labels(method=method, handler=handler_name).observe(
                    after_time - before_time
                )
                REQUEST_COUNT.labels(
                    method=method, handler=handler_name, code=response.status_code
                ).inc()
            finally:
                REQUESTS_INPROGRESS.labels(method=method, handler=handler_name).dec()
            return response

        return custom_handler


async def handle_errors(request: Request, exc):
    """
    overrides the default error handler defined in ServerErrorMiddleware
    """
    exception("unhandled_error")
    return PlainTextResponse("Internal Server Error", status_code=500)
