from enum import Enum
from pathlib import Path


# from http import HTTPMethod  # python3.11+

class HTTPMethod(str, Enum):
    HEAD = 'HEAD'
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    PUT = 'PUT'


class ServiceMode(str, Enum):
    SAAS = 'saas'
    ONPREM = 'onprem'
    PRIVATE = 'private'


class Env(str, Enum):
    default: str | None

    def __new__(cls, value: str, default: str | None = None):
        """
        All environment variables and optionally their default values.
        Since envs always have string type the default value also should be
        of string type and then converted to the necessary type in code.
        There is no default value if not specified (default equal to None)
        """
        obj = str.__new__(cls, value)
        obj._value_ = value

        obj.default = default
        return obj

    # in case want to remove the default value: adjust environment service
    # after that
    SECRET_KEY = 'MODULAR_API_SECRET_KEY'
    MODE = 'MODULAR_API_MODE', ServiceMode.SAAS.value
    API_CALLS_PER_SECOND_LIMIT = 'MODULAR_API_CALLS_PER_SECOND_LIMIT', '10'
    MIN_CLI_VERSION = 'MODULAR_API_MIN_CLI_VERSION', '1.2.0'
    ENABLE_PRIVATE_MODE = 'MODULAR_API_ENABLE_PRIVATE_MODE', 'false'

    # logs
    SERVER_LOG_LEVEL = 'MODULAR_API_SERVER_LOG_LEVEL', 'INFO'
    CLI_LOG_LEVEL = 'MODULAR_API_CLI_LOG_LEVEL', 'INFO'
    LOG_PATH = ('MODULAR_API_LOG_PATH',
                str((Path.home() / '.modular_api/log').resolve()))

    MONGO_URI = 'MODULAR_API_MONGO_URI'
    MONGO_DATABASE = 'MODULAR_API_MONGO_DATABASE'
    MONGO_RATE_LIMITS_DATABASE = ('MODULAR_API_RATE_LIMITS_MONGO_DATABASE',
                                  'modular-api-rate-limits')

    AWS_REGION = 'AWS_REGION', 'us-east-1'


ACTIVATED_STATE = 'activated'
API_MODULE_FILE = 'api_module.json'
BLOCKED_STATE = 'blocked'
CLI_PATH_KEY = 'cli_path'
CLI_VIEW = 'cli'
COMMAND = 'command'
COMMANDS_BASE_FILE_NAME = 'web_service/commands_base.json'
DATE = 'date'
DATE_FORMAT = '%d-%m-%Y'
DEPENDENCIES = 'dependencies'
EVENT_TYPE = 'event_type'
EVENT_TYPE_API = 'api'
GROUP = 'group'
ID = 'id'
JOB_ID = 'job_id'
KEY = 'key'
LINUX = 'posix'
API_LOG_FILE_NAME = 'modular_api.log'
CLI_LOG_FILE_NAME = 'modular_api_cli.log'
LOGS_FORMAT = '[%(asctime)s] [%(levelname)s] [%(dd.trace_id)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
LOG_FOLDER = '.modular_api'
MAX_COLUMNS_WIDTH = 30
META = 'meta'
MIN_VER = 'min_version'
MODULAR_API_CODE = 'Code'
MODULAR_API_ITEMS = 'items'
MODULAR_API_JSON_CODE = 'code'
MODULAR_API_JSON_MESSAGE = 'message'
MODULAR_API_JSON_WARNINGS = 'warnings'
MODULAR_API_MESSAGE = 'Message'
MODULAR_API_RESPONSE = 'Response'
MODULAR_API_TABLE_TITLE = 'table_title'
MODULAR_API_USERNAME = 'modular_admin_username'
MODULAR_API_WARNINGS = 'Warnings'
MODULES_DIR = 'modules'
MODULES_PATH = 'modules'
MODULE_NAME_KEY = 'module_name'
MOUNT_POINT_KEY = 'mount_point'
M_POINT = 'mount_point'
MODULE_NAME = 'module_name'
PRODUCT = 'product'
REMOVED_STATE = 'removed'
STATS_DB_NAME = 'ModularStats.json'
STATUS = 'status'
TABLE_VIEW = 'table'
TIMESTAMP = 'timestamp'
TOOL_VERSION_MAPPING = """\n{tool}        {version}"""
WINDOWS = 'nt'

SWAGGER_HTML = \
"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="SwaggerUI" />
    <title>SwaggerUI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui.css" />
  </head>
  <body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-bundle.js" crossorigin></script>
  <script src="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-standalone-preset.js" crossorigin></script>
  <script>
    window.onload = () => {{
      window.ui = SwaggerUIBundle({{
        url: '{url}',
        dom_id: '#swagger-ui',
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout",
      }});
    }};
  </script>
  </body>
</html>
"""

SERVICE_NAME = 'service_name'
SERVICE_DISPLAY_NAME = 'service_display_name'
ALLOWED_VALUES = 'allowed_values'
AUX_DATA = 'aux_data'
MODULAR_USER_META_TYPES = (ALLOWED_VALUES, AUX_DATA)
