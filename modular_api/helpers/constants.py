import getpass

USER_NAME = getpass.getuser()
SUPPORTED_OS = ['nt', 'posix']
LOG_FORMAT_FOR_FILE = f'%(asctime)s [USER: {USER_NAME}][%(levelname)s]' \
                      f'%(name)s,%(lineno)s [Trace ID: %(dd.trace_id)s] ' \
                      f'%(message)s'

ACTIVATED_STATE = 'activated'
API_MODULE_FILE = 'api_module.json'
BLOCKED_STATE = 'blocked'
CLI_PATH_KEY = 'cli_path'
CLI_VIEW = 'cli'
COMMANDS_BASE_FILE_NAME = 'web_service/commands_base.json'
CUSTOM_LOG_PATH = 'LOG_PATH'
DEPENDENCIES = 'dependencies'
HTTP_OK = 200
LINUX = 'posix'
LOG_FILE_NAME = 'modular_api.log'
LOG_FOLDER = '.modular_api'
MAX_COLUMNS_WIDTH = 30
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
MODULE_NAME_KEY = 'module_name'
MODULES_PATH = 'modules'
MODULES_DIR = 'modules'
MOUNT_POINT_KEY = 'mount_point'
REMOVED_STATE = 'removed'
SWAGGER_ENABLED_KEY = 'swagger_enabled'
TABLE_VIEW = 'table'
TOOL_VERSION_MAPPING = """\n{tool}        {version}"""
USERNAME_ATTR = 'username'
WINDOWS = 'nt'
