from apistar import App, Include
from api.urls import api_urls
from utils.settings import SettingsComponent


routes = [
    Include('/v1', name='v1', routes=api_urls),
]

components = [
    SettingsComponent('IDUNN'),
]

app = App(routes=routes, schema_url='/schema', components=components)


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, debug=True)
