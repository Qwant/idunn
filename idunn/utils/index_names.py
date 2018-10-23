from inspect import Parameter
from apistar import Component
from elasticsearch import Elasticsearch
from .settings import Settings

class IndexNames(dict):
    """
        Class to handle the names of the indices from the settings
    """

class IndexNamesSettingsComponent(Component):
    def __init__(self) -> None:
        self._indices = None

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        return parameter.annotation is IndexNames

    def resolve(self, settings: Settings) -> IndexNames:
        if not self._indices:
            self._make_indices(settings)
        return self._indices

    def _make_indices(self, settings) -> IndexNames:
        self._indices = {
            "admin": settings['PLACE_ADMIN_INDEX'],
            "street": settings['PLACE_STREET_INDEX'],
            "address": settings['PLACE_ADDRESS_INDEX'],
            "poi": settings['PLACE_POI_INDEX'],
        }
