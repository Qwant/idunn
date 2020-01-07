from idunn import settings
from idunn.utils.logging import init_logging, handle_errors
from idunn.api.urls import get_api_urls
from idunn.utils.encoders import override_datetime_encoder

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Mount

from starlette_prometheus import PrometheusMiddleware

import uvicorn


init_logging(settings)

routes = [
    Mount('/v1', routes=get_api_urls(settings)),
]

app = FastAPI(routes=routes, title="Idunn", debug=__name__ == '__main__')


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = await call_next(request)
    # TODO: only set it when there is an Origin header!
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(f'Invalid parameter received: {str(exc)}', status_code=404)


app.add_middleware(PrometheusMiddleware)
app.add_exception_handler(Exception, handle_errors)
override_datetime_encoder()

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="debug")
