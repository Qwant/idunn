from idunn import settings
from idunn.api.urls import get_api_urls
from idunn.utils.encoders import override_datetime_encoder
from idunn.utils.prometheus import handle_errors
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from urllib.parse import urlparse


# Setup docs settings
base_url = settings["BASE_URL"]
# path_prefix = settings["URL_PATH_PREFIX"]
# root_path = urlparse(base_url).path.rstrip("/")
root_path = "/maps/detail"
docs_settings = {}
if not settings["DOCS_ENABLED"]:
    docs_settings.update({"openapi_url": None, "redoc_url": None, "docs_url": None})
else:
    docs_settings.update(
        {"openapi_url": "/openapi.json", "redoc_url": "/redoc", "docs_url": "/docs"}
    )

# Setup FastAPI app
app = FastAPI(
    title="Idunn", version="0.2", debug=__name__ == "__main__", root_path=root_path, **docs_settings
)
v1_routes = get_api_urls(settings)
app.include_router(APIRouter(routes=v1_routes))  # , prefix=path_prefix)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["CORS_ALLOW_ORIGINS"].split(","),
    allow_headers=settings["CORS_ALLOW_HEADERS"].split(","),
)

# Override FastAPI defaults
app.add_exception_handler(Exception, handle_errors)
override_datetime_encoder()

if __name__ == "__main__":
    import logging

    logging.getLogger().setLevel("DEBUG")
    uvicorn.run(app, host="127.0.0.1", port=5000)
