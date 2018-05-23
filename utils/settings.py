import os
import apistar_settings
import yaml


def _load_yaml_file(file):
    with open(file, 'r') as default:
        return yaml.load(default)


class SettingsComponent(apistar_settings.SettingsComponent):
    """
    APIStar component to load settings

    It merges settings from different sources:
    - the settings found in the default_settings.yaml
    - a yaml settings file given with an env var ({project}_CONFIG_FILE, eg. IDUNN_CONFIG_FILE)
    - env var only for already existing settings.
        The env var need to be defined as {project}_{var_name} eg. IDUNN_ES to override the "ES" settings.
    """

    def __init__(self, project_name) -> None:
        self.settings = {}
        self._load_default_config()

        self._load_specific_config(project_name)

        self._load_from_env_var(project_name)

        print(f"config: {self.settings}")

    def _load_default_config(self):
        """
        load the default config from a default_settings.yaml in the same directory
        """
        default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'default_settings.yaml')
        self.settings.update(_load_yaml_file(default_config_path))

    def _load_specific_config(self, project_name):
        """
        load settings from a yaml file whose pth in given
        with the env var {project}_CONFIG_FILE (eg. IDUNN_CONFIG_FILE for the IDUNN project)
        """
        path = os.environ.get(f'{project_name}_CONFIG_FILE')
        if not path:
            return
        config_path = path
        self.settings.update(_load_yaml_file(config_path))

    def _load_from_env_var(self, project_name):
        """
        overrides existing settings from the env var.
        The env var need to be defined as {project}_{var_name}
        eg. IDUNN_ES to override the "ES" settings in the IDUNN project.
        """
        for k in self.settings.keys():
            ovverided_value = os.environ.get(f'{project_name}_{k}')
            if ovverided_value:
                self.settings[k] = ovverided_value
