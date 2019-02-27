import os
from inspect import Parameter
from apistar import Component
from .settings import Settings
from elasticsearch import Elasticsearch
from .settings import _load_yaml_file

class Categories(dict):
    """
        Class to handle the possible categories of places to fetch
    """

class CategoriesComponent(Component):
    def __init__(self) -> None:
        self._categories = None

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is Categories

    def resolve(self, settings: Settings) -> Categories:
        if not self._categories:
            self._make_categories(settings)
        return self._categories

    def _make_categories(self, settings) -> Categories:
        filename = settings['CATEGORIES_FILENAME']
        categories_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
        if categories_path:
            self._categories = _load_yaml_file(categories_path)
