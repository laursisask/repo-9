AVAILABLE_COMMANDS_CONFIG = 'available_commands'
DEFAULT_CONFIG_FILE_NAME = 'startup_config.json'


class Config:
    def __init__(self):
        self.config = {}

    def set_available_commands(self, available_commands):
        self.config[AVAILABLE_COMMANDS_CONFIG] = available_commands

    @property
    def available_commands(self):
        return self.config.get(AVAILABLE_COMMANDS_CONFIG)
