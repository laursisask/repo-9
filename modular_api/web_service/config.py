import json
import os
from pathlib import Path

import click

from modular_api.helpers.decorators import ExceptionDecorator
from modular_api.helpers.exceptions import ModularApiInternalException, \
    ModularApiConfigurationException

PORT_CONFIG = 'port'
HOST_CONFIG = 'host'
PREFIX_CONFIG = 'url_prefix'
INIT_ONLY_CONFIG = 'init_only'
LOGGING_CONFIG = 'logging'
SECRET_PASSPHRASE = 'secret_passphrase'
MODE = 'mode'
IS_PRIVATE_MODE_ENABLED = 'is_private_mode_enabled'
AVAILABLE_COMMANDS_CONFIG = 'available_commands'
IS_SWAGGER_ENABLED_BY_DEFAULT = False
DEFAULT_SWAGGER_PATH = '/swagger'
DEFAULT_CONFIG_FILE_NAME = 'startup_config.json'


class Config:

    def _load_config(self):
        with open(self.file_name, 'r+') as config_file:
            file_content = config_file.read()

        try:
            json_content = json.loads(file_content)
            self.config = json_content
        except Exception:
            raise ModularApiInternalException(
                'Error occurred while loading app configuration')

    def __init__(self, file_name=DEFAULT_CONFIG_FILE_NAME):
        self.file_name = Path(__file__).parent.parent / file_name
        self._load_config()
        self.check_required_options(required_options=[PORT_CONFIG, HOST_CONFIG,
                                                      MODE, SECRET_PASSPHRASE])

    @property
    def secret_passphrase(self):
        return self.config.get(SECRET_PASSPHRASE)

    @property
    def mode(self):
        return self.config.get(MODE)

    @property
    def is_private_mode_enabled(self):
        return self.config.get(IS_PRIVATE_MODE_ENABLED, False)

    @property
    def logging(self):
        return self.config.get(LOGGING_CONFIG)

    @property
    def host(self):
        return self.config.get(HOST_CONFIG)

    @property
    def port(self):
        return self.config.get(PORT_CONFIG)

    @property
    def prefix(self):
        return self.config.get(PREFIX_CONFIG)

    @property
    def swagger_ui_is_enabled(self):
        swagger_ui_conf = self.config.get('swagger-ui')
        if not swagger_ui_conf:
            return IS_SWAGGER_ENABLED_BY_DEFAULT
        return swagger_ui_conf.get('enable')

    @property
    def swagger_ui_path(self):
        swagger_ui_conf = self.config.get('swagger-ui')
        if not swagger_ui_conf:
            return DEFAULT_SWAGGER_PATH
        return swagger_ui_conf.get('path')

    @property
    def tracer_path_to_save_data(self):
        tracing_conf = self.config.get('tracing')
        if not tracing_conf:
            return ''
        return tracing_conf.get('path_to_save_data')

    def set_available_commands(self, available_commands):
        self.config[AVAILABLE_COMMANDS_CONFIG] = available_commands

    @ExceptionDecorator(click.echo, 'Missed required options')
    def check_required_options(self, required_options):
        missed_options = [option for option in required_options
                          if not self.config.get(option)]
        if missed_options:
            raise ModularApiConfigurationException(
                f'Missed required options in {DEFAULT_CONFIG_FILE_NAME}:'
                f'{os.linesep}{", ".join(missed_options)}')

    @property
    def available_commands(self):
        return self.config.get(AVAILABLE_COMMANDS_CONFIG)

    @property
    def minimal_allowed_cli_version(self):
        return self.config.get('minimal_allowed_cli_version')
