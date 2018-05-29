from apistar import App, Include

from idunn.utils.settings import SettingsComponent
from idunn.utils.es_wrapper import ElasticSearchComponent
from idunn.api.urls import api_urls


routes = [
    Include('/v1', name='v1', routes=api_urls),
]

components = [
    SettingsComponent('IDUNN'),
    ElasticSearchComponent()
]

app = App(routes=routes, schema_url='/schema', components=components)


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, debug=True)
