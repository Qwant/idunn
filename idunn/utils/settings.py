import os
import yaml
from typing import Any
from inspect import Parameter
import logging
from apistar import Component


def _load_yaml_file(file):
    with open(file, 'r') as default:
        return yaml.load(default)


class Settings(dict):
    """The type of settings dictionaries.
    Annotate your handler parameters with this to have a settings
    dictionary injected into those handlers.

    This is heavily inspired from https://github.com/Bogdanp/apistar_settings
    """


class SettingsComponent(Component):
    """
    APIStar component to load settings

    It merges settings from different sources:
    - the settings found in the default_settings.yaml
    - a yaml settings file given with an env var ({project}_CONFIG_FILE, eg. IDUNN_CONFIG_FILE)
    - env var only for already existing settings.
        The env var need to be defined as {project}_{var_name} eg. IDUNN_ES to override the "ES" settings.
    """

    def __init__(self, project_name) -> None:
        self._settings = Settings()
        self._load_default_config()

        self._load_specific_config(project_name)

        self._load_from_env_var(project_name)

        logging.getLogger(__name__).debug(f"config: {self._settings}")

    def _load_default_config(self):
        """
        load the default config from a default_settings.yaml in the same directory
        """
        default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'default_settings.yaml')
        self._settings.update(_load_yaml_file(default_config_path))

    def _load_specific_config(self, project_name):
        """
        load settings from a yaml file whose pth in given
        with the env var {project}_CONFIG_FILE (eg. IDUNN_CONFIG_FILE for the IDUNN project)
        """
        path = os.environ.get(f'{project_name}_CONFIG_FILE')
        if path:
            self._settings.update(_load_yaml_file(path))

    def _load_from_env_var(self, project_name):
        """
        overrides existing settings from the env var.
        The env var need to be defined as {project}_{var_name}
        eg. IDUNN_ES to override the "ES" settings in the IDUNN project.
        """
        for k in self._settings.keys():
            ovveriden_value = os.environ.get(f'{project_name}_{k}')
            if ovveriden_value:
                self._settings[k] = ovveriden_value

    def can_handle_parameter(self, parameter: Parameter) -> bool:
        # Micro-optimization given that we know that this component
        # only ever injects values of type Settings.
        return parameter.annotation is Settings

    def resolve(self) -> Settings:
        return self._settings

    def __getattr__(self, name: str) -> Any:
        return getattr(self._settings, name)

    def __getitem__(self, name: str) -> Any:
        return self._settings[name]
