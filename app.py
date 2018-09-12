from apistar import App, Include

from idunn.utils.settings import SettingsComponent
from idunn.utils.es_wrapper import ElasticSearchComponent
from idunn.utils.cors import CORSHeaders
from idunn.api.urls import api_urls

from apistar_prometheus import PrometheusComponent, PrometheusHooks

routes = [
    Include('/v1', name='v1', routes=api_urls),
]

settings = SettingsComponent('IDUNN')
components = [
    settings,
    ElasticSearchComponent(),
    PrometheusComponent()
]

event_hooks = [CORSHeaders, PrometheusHooks()]


app = App(
    routes=routes,
    schema_url='/schema',
    components=components,
    event_hooks=event_hooks
)


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, debug=True)
