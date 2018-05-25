from inspect import Parameter
from apistar import Component
from elasticsearch import Elasticsearch


class ElasticSearchComponent(Component):

    def __init__(self, settings) -> None:
        self._settings = settings
        self._es = None

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Elasticsearch

    def resolve(self) -> Elasticsearch:
        if not self._es:
            # the client is lazily created for the tests
            self._make_client()
        return self._es

    def _make_client(self) -> Elasticsearch:
        self._es = Elasticsearch(self._settings['ES_URL'])
