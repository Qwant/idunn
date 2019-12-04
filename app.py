from apistar import Include

from idunn import settings
from idunn.utils.index_names import IndexNamesSettingsComponent
from idunn.utils.es_wrapper import ElasticSearchComponent
from idunn.utils.logging import init_logging, LogErrorHook
from idunn.utils.cors import CORSHeaders
from idunn.utils.app import IdunnApp
from idunn.api.urls import get_api_urls
from idunn.utils.prometheus import PrometheusComponent, PrometheusHooks

init_logging(settings)

routes = [
    Include('/v1', name='v1', routes=get_api_urls(settings)),
]

components = [
    settings,
    ElasticSearchComponent(),
    IndexNamesSettingsComponent(),
    PrometheusComponent()
]

# WARNING: using Classes (and not instances) in hooks list causes a memory leak.
# See https://github.com/encode/apistar/issues/606 for more details
event_hooks = [LogErrorHook(), CORSHeaders(), PrometheusHooks()]


app = IdunnApp(
    routes=routes,
    schema_url='/schema',
    components=components,
    event_hooks=event_hooks
)


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, debug=True)
