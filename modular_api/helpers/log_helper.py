from ddtrace import patch_all
patch_all(logging=True)

import logging
import logging.config
import os
from pathlib import Path

from modular_api.helpers.constants import (
    API_LOG_FILE_NAME,
    CLI_LOG_FILE_NAME,
    Env,
    LOGS_FORMAT
)


def _get_logs_path() -> Path:
    """
    Returns logs that exists
    :return:
    """
    path = os.getenv(Env.LOG_PATH, Env.LOG_PATH.default)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        default = Env.LOG_PATH.default
        logging.getLogger().warning(
            f'Cannot access {path}. Writing logs to {default}'
        )
        path = default
        os.makedirs(path, exist_ok=True)
    return Path(path).resolve()


LOGS_PATH = _get_logs_path()
API_LOGS_FILE = LOGS_PATH / API_LOG_FILE_NAME
CLI_LOGS_FILE = LOGS_PATH / CLI_LOG_FILE_NAME

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        # 'console_formatter': {
        #     'format': LOGS_FORMAT
        # },
        'file_formatter': {
            'format': LOGS_FORMAT
        }
    },
    'handlers': {
        # 'console_handler': {
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'console_formatter'
        # },
        'api_file_handler': {
            'class': 'logging.FileHandler',
            'filename': API_LOGS_FILE,
            'formatter': 'file_formatter',
        },
        'cli_file_handler': {
            'class': 'logging.FileHandler',
            'filename': CLI_LOGS_FILE,
            'formatter': 'file_formatter',
        }
    },
    'loggers': {
        'modular_api': {
            'level': os.getenv(Env.SERVER_LOG_LEVEL,
                               Env.SERVER_LOG_LEVEL.default),
            'handlers': ['api_file_handler']  # + 'console_handler'
        },
        'modular_api_cli': {
            'level': os.getenv(Env.CLI_LOG_LEVEL, Env.CLI_LOG_LEVEL.default),
            'handlers': ['cli_file_handler']
        }
    }
})


def get_logger(name: str, level=None) -> logging.Logger:
    log = logging.getLogger(name)
    if level:
        log.setLevel(level)
    return log


def init_console_handler():
    # todo, since modular_api_cli module reuses a lot of code from
    #  modular_api module we cannot add logging.StreamHandler to modular_api.*
    #  logger because than each cli command will output a lot of junk. So,
    #  I think we should not use modules from modular_api in CLI. But
    #  for now this kludge: add StreamHandler only of server is running
    #  (this function is used only when user stars the server)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(LOGS_FORMAT))
    logging.getLogger('modular_api').addHandler(h)
