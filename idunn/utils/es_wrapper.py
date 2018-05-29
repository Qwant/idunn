from inspect import Parameter
from apistar import Component
from elasticsearch import Elasticsearch
from .settings import Settings


class ElasticSearchComponent(Component):

    def __init__(self) -> None:
        self._es = None

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Elasticsearch

    def resolve(self, settings: Settings) -> Elasticsearch:
        if not self._es:
            # the client is lazily created for the tests
            self._make_client(settings)
        return self._es

    def _make_client(self, settings) -> Elasticsearch:
        self._es = Elasticsearch(settings['ES_URL'])
