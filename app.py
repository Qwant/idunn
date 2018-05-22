from apistar import App, Include
from api.urls import api_urls


routes = [
    Include('/v1', name='v1', routes=api_urls),
]

app = App(routes=routes, schema_url='/schema')


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, debug=True)
