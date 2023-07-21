import importlib.util
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from unittest.mock import MagicMock

import beaker.middleware
import pkg_resources
from bottle import (default_app, run, route, request, BaseRequest,
                    get, view, post, redirect, hook)
from ddtrace import tracer
from pynamodb.exceptions import GetError
from swagger_ui import api_doc

from services.permissions_cache_service import permissions_handler_instance
from helpers.request_processor import generate_route_meta_mapping
from helpers.response_processor import process_response
from commands_generator import (resolve_group_name,
                                get_file_names_which_contains_admin_commands)
from helpers.compatibility_check import CompatibilityChecker
from helpers.exceptions import (ModularApiUnauthorizedException,
                                ModularApiBadRequestException,
                                ModularApiConfigurationException)
from helpers.jwt_auth import encode_data_to_jwt, username_from_jwt_token, \
    decode_jwt_token
from helpers.log_helper import get_logger, exception_handler_formatter
from helpers.params_converter import convert_api_params
from helpers.response_utils import get_trace_id, build_response
from helpers.utilities import prepare_request_path, token_from_auth_header
from helpers.constants import HTTP_OK, MODULES_PATH, MODULE_NAME_KEY
from helpers.constants import MODULAR_API_USERNAME, SWAGGER_ENABLED_KEY, \
    COMMANDS_BASE_FILE_NAME, API_MODULE_FILE, MOUNT_POINT_KEY
from swagger.generate_open_api_spec import associate_definition_with_group
from web_service import META_VERSION_ID
from web_service.config import Config
from web_service.response_processor import (build_exception_content,
                                            validate_request,
                                            extract_and_convert_parameters,
                                            get_group_path)
from web_service.settings import SESSION_SETTINGS, SWAGGER_SETTINGS

_LOG = get_logger('index')

MODULE_GROUP_GROUP_OBJECT_MAPPING = {}
CONFIG = Config()
SWAGGER_PATH = CONFIG.swagger_ui_path
tracer.configure(writer=MagicMock())
WEB_SERVICE_PATH = os.path.dirname(__file__)

SWAGGER_ALLOWED_PATH = []

PERMISSION_SERVICE = permissions_handler_instance()


def resolve_permissions(tracer, empty_cache=None):
    def decorator(func):
        def wrapper(*a, **ka):
            user, password = request.auth or (None, None)
            token = None
            if not password:  # not basic auth -> probably bearer
                header = request.headers.get('Authorization')
                token = token_from_auth_header(header) if header else None
            try:
                allowed_commands, user_meta = \
                    PERMISSION_SERVICE.authenticate_user(
                        username=user,
                        password=password,
                        token=token,
                        empty_cache=empty_cache
                    )
                ka['allowed_commands'] = allowed_commands
                ka['user_meta'] = user_meta
                return func(*a, **ka)
            except (ModularApiUnauthorizedException,
                    ModularApiConfigurationException,
                    GetError) as e:
                _trace_id = get_trace_id(tracer=tracer)
                exception_handler_formatter(
                    logger=_LOG,
                    exception=e,
                    trace_id=_trace_id
                )
                code, content = build_exception_content(exception=e)
                error_response = build_response(_trace_id=_trace_id,
                                                http_code=code,
                                                content=content)
                return error_response

        return wrapper

    return decorator


def get_module_group_and_associate_object():
    modules_path = MODULES_PATH
    global MODULE_GROUP_GROUP_OBJECT_MAPPING
    for module in os.listdir(modules_path):
        module_api_config = os.path.join(modules_path, module,
                                         API_MODULE_FILE)
        with open(module_api_config) as file:
            api_config = json.load(file)

        module_path = os.path.join(modules_path, module)
        if module_path not in sys.path:
            sys.path.append(module_path)

        cli_path = api_config['cli_path']
        mount_point = api_config['mount_point']

        command_group_path = os.path.join(modules_path, module,
                                          *cli_path.split('/'))
        listdir = get_file_names_which_contains_admin_commands(
            path_to_scan=command_group_path)
        for command_group in listdir:
            group_full_name_list, group_name = resolve_group_name(
                group_file=command_group)
            is_private_group = (type(group_full_name_list) == list and
                                group_full_name_list[0] == 'private' or
                                group_full_name_list == 'private')

            if is_private_group ^ CONFIG.is_private_mode_enabled:
                continue
            group_path = get_group_path(mount_point=mount_point,
                                        group_name=group_name)
            module_spec = importlib.util.spec_from_file_location(
                group_name,
                os.path.join(command_group_path, command_group))
            imported_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(imported_module)
            MODULE_GROUP_GROUP_OBJECT_MAPPING.update(
                {group_path: imported_module})
    return MODULE_GROUP_GROUP_OBJECT_MAPPING


def _initialize():
    # loading configuration
    commands_base_path = os.path.join(WEB_SERVICE_PATH,
                                      COMMANDS_BASE_FILE_NAME)
    if not os.path.exists(commands_base_path):
        raise ModularApiConfigurationException(
            'Can not run server without any installed modules')

    with open(commands_base_path) as file:
        valid_commands = json.load(file)

    CONFIG.set_available_commands(
        available_commands=valid_commands)
    _LOG.info('[init] Commands base phase completed')

    host = CONFIG.host
    port = CONFIG.port
    get_module_group_and_associate_object()
    return host, port


@route('/doc', method='GET')
@route(f'{CONFIG.prefix}/doc', method='GET')
@tracer.wrap()
@resolve_permissions(tracer=tracer)
def web_help(allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    return build_response(
        _trace_id=_trace_id,
        http_code=HTTP_OK,
        content={'available_commands': allowed_commands},
        message="This is the Modular-API administration tool. "
                "To request support, please contact "
                "Modular Support Team")


@route('/doc/<path:path>', method='GET')
@route(f'{CONFIG.prefix}/doc/<path:path>', method='GET')
@tracer.wrap()
@resolve_permissions(tracer=tracer)
def generate_group_or_command_help(path, allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    path = prepare_request_path(path=request.path, prefix=CONFIG.prefix). \
        replace('/doc', '')

    route_meta_mapping = generate_route_meta_mapping(
        commands_meta=allowed_commands)

    requested_command = []
    requested_commands = []
    for itinerary, command_meta in route_meta_mapping.items():
        if path in itinerary:
            requested_commands.append(command_meta)
        elif path == itinerary:
            requested_command.append(command_meta)

    if not any((requested_command, requested_commands)):
        return build_response(
            _trace_id=_trace_id,
            http_code=404,
            message='Can not found requested resource')

    return build_response(
        _trace_id=_trace_id,
        http_code=HTTP_OK,
        content={
            'available_commands': requested_command or requested_commands},
        message="This is the Modular-API administration tool. "
                "To request support, please contact "
                "Modular Support Team")


def __validate_cli_version(_trace_id):
    version_warning = None
    error_response = None
    try:
        version_warning = CompatibilityChecker().check_compatibility(
            request=request,
            allowed_version=CONFIG.minimal_allowed_cli_version
        )
        return version_warning, error_response
    except ModularApiBadRequestException as e:
        exception_handler_formatter(
            logger=_LOG,
            exception=e,
            trace_id=_trace_id
        )

        code, content = build_exception_content(exception=e)
        error_response = build_response(_trace_id=_trace_id,
                                        http_code=code,
                                        content=content)
        return version_warning, error_response


@route('/login', method=['GET'])
@route(f'{CONFIG.prefix}/login', method=['GET'])
@tracer.wrap()
@resolve_permissions(tracer=tracer, empty_cache=True)
def login(allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    version_warning, error_response = __validate_cli_version(
        _trace_id=_trace_id
    )
    if error_response:
        return error_response

    username, _ = request.auth
    meta_param = request.params.dict.get('meta')
    meta_return = False
    if meta_param:
        if isinstance(meta_param, list) and meta_param:
            meta_return = meta_param[0]
        meta_return = True if meta_return.lower() == 'true' else False
    jwt_token = encode_data_to_jwt(username=username)
    data = {
        'jwt': jwt_token,
        'version': __resolve_version()
    }
    if meta_return:
        data['meta'] = add_versions_to_allowed_modules(
            allowed_commands=allowed_commands)
    if version_warning:
        data['warnings'] = version_warning

    return build_response(_trace_id=_trace_id, http_code=HTTP_OK, content=data)


@lru_cache()
def __resolve_version():
    from version import modular_api_version as version
    return version


def add_versions_to_allowed_modules(allowed_commands: dict):
    # todo refactor with resolve_user_available_components_version ASAP
    modules_path = Path(MODULES_PATH)
    for module in modules_path.iterdir():
        api_file_path = module / API_MODULE_FILE
        if not module.is_dir() or not api_file_path.exists():
            continue
        with open(str(api_file_path), 'r') as file:
            module_descriptor = json.load(file)

        mount_point = module_descriptor[MOUNT_POINT_KEY]
        if mount_point in allowed_commands.keys():
            allowed_commands[mount_point]['version'] = pkg_resources. \
                get_distribution(
                module_descriptor[MODULE_NAME_KEY]
            ).version
    return allowed_commands


def resolve_user_available_components_version(allowed_commands: dict):
    modules_path = Path(__file__).parent.parent / 'modules'
    components_versions = {}
    for module in modules_path.iterdir():
        api_file_path = module / API_MODULE_FILE
        if not module.is_dir() or not api_file_path.exists():
            continue
        with open(str(api_file_path), 'r') as file:
            module_descriptor = json.load(file)
        if module_descriptor[MOUNT_POINT_KEY] in allowed_commands.keys():
            module_name = module_descriptor[MODULE_NAME_KEY]
            components_versions[module_name] = pkg_resources.get_distribution(
                module_name
            ).version
    return components_versions


@route('/version', method=['GET'])
@route(f'{CONFIG.prefix}/version', method=['GET'])
@tracer.wrap()
@resolve_permissions(tracer=tracer, empty_cache=False)
def version(allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    resolve_user_available_components_version(allowed_commands)
    data = {
        'modular_api': __resolve_version(),
    }
    components_version = resolve_user_available_components_version(
        allowed_commands
    )
    if components_version:
        data['components_version'] = components_version
    response_template = {
        "items": data,
        "table_title": 'User available component(s) version',
        "warnings": [],
        "message": None
    }
    return build_response(
        _trace_id=_trace_id,
        http_code=HTTP_OK,
        content=response_template
    )


@route('/health_check', method=['GET'])
@route(f'{CONFIG.prefix}/health_check', method=['GET'])
@tracer.wrap()
def version():
    _trace_id = get_trace_id(tracer=tracer)
    return build_response(
        _trace_id=_trace_id,
        http_code=HTTP_OK,
        content=None
    )


def __automated_relogin() -> bool:
    header = request.headers.get('Authorization')
    raw_token = header.split(maxsplit=2)[-1]
    token = decode_jwt_token(raw_token)
    client_meta_version = token.get('meta_version')
    if client_meta_version == META_VERSION_ID:
        return False
    return True


@route('/<group>/<command>', method=['POST', 'GET'])
@route('/<mount_point>/<group>/<command>', method=['POST', 'GET'])
@route('/<mount_point>/<group>/<subgroup>/<command>', method=['POST', 'GET'])
@route('/<mount_point>/<parent_group>/<group>/<subgroup>/<command>',
       method=['POST', 'GET'])
@route(f'{CONFIG.prefix}/<group>/<command>',
       method=['POST', 'GET'])
@route(f'{CONFIG.prefix}/<mount_point>/<group>/<command>',
       method=['POST', 'GET'])
@route(f'{CONFIG.prefix}/<mount_point>/<group>/<subgroup>/<command>',
       method=['POST', 'GET'])
@route(
    f'{CONFIG.prefix}/<mount_point>/<parent_group>/<group>/<subgroup>/<command>',
    method=['POST', 'GET'])
@tracer.wrap()
@resolve_permissions(tracer=tracer)
def index(mount_point=None, group=None, command=None, parent_group=None,
          subgroup=None, allowed_commands=None, user_meta=None):
    _trace_id = get_trace_id(tracer=tracer)
    temp_files_list = []
    try:
        relogin_needed = __automated_relogin()
        auth_type = request.headers.get('authorization')
        if auth_type and auth_type.startswith('Basic'):
            relogin_needed = False
        if relogin_needed:
            # if you are going to change exception message - please change
            # correspond text in Modular-CLI
            raise ModularApiUnauthorizedException(
                    'The provided token has expired due to updates in '
                    'commands meta. Please get a new token from \'/login\' '
                    'resource')
        version_warning, error_response = __validate_cli_version(
            _trace_id=_trace_id
        )
        if error_response:
            return error_response

        path = prepare_request_path(path=request.path,
                                    prefix=CONFIG.prefix)
        method = request.method

        route_meta_mapping = generate_route_meta_mapping(
            commands_meta=allowed_commands)

        command_def = route_meta_mapping.get(path)
        if not command_def:
            raise ModularApiBadRequestException('Can not found requested '
                                               'command')
        request_body_raw = extract_and_convert_parameters(
            request=request,
            command_def=command_def)

        request_body_raw = validate_request(command=command_def,
                                            req_params=request_body_raw,
                                            method=method,
                                            user_meta=user_meta)

        secure_parameters = command_def.get('secure_parameters', [])
        parameters, temp_files_list, body_to_log = \
            convert_api_params(
                body=request_body_raw,
                command_def=command_def,
                secure_parameters=secure_parameters
            )
        _LOG.info('Request data: \npath={}\n'
                  'method={}\nbody:\n{}'.format(path, method, body_to_log))

        command_handler_name = command_def.get('handler')
        group_name = command_def.get('parent')
        mount_point = command_def.get('mount_point')
        group_path = get_group_path(mount_point=mount_point,
                                    group_name=group_name)

        correct_method = getattr(
            MODULE_GROUP_GROUP_OBJECT_MAPPING[group_path],
            command_handler_name)
        # todo get username from user_meta of somewhere else, but
        #  not from header again.
        username = username_from_jwt_token(
            token_from_auth_header(request.headers.get('Authorization'))
        )
        # hopefully, token will be here... otherwise 500, I mean, it must be
        # here because the endpoint is authorized by token
        response = correct_method.main(
            args=parameters,
            standalone_mode=False,
            obj={MODULAR_API_USERNAME: username}
        )
        # obj goes to click.Context. Other module CLI should use it to
        # understand what user is making the request
        response = json.loads(response)
        _LOG.info(f'Obtained response {response} for {_trace_id} request')
        content, code = process_response(response=response)
        if content.get('warnings'):
            if version_warning:
                content['warnings'].extend(version_warning)
        else:
            content['warnings'] = version_warning
        return build_response(_trace_id=_trace_id,
                              http_code=code,
                              content=content)

    except Exception as e:
        exception_handler_formatter(
            logger=_LOG,
            exception=e,
            trace_id=_trace_id
        )
        code, content = build_exception_content(exception=e)
        error_response = build_response(_trace_id=_trace_id,
                                        http_code=code,
                                        content=content)
        return error_response
    finally:
        if temp_files_list:
            for each_file in temp_files_list:
                os.remove(each_file)


def swagger_login(swagger_path):
    @get(swagger_path)
    @view('login_swagger')
    @tracer.wrap()
    def swagger_login_get():
        return {'swagger_path': swagger_path}


def swagger_auth(swagger_path):
    @post(swagger_path)
    @tracer.wrap()
    def swagger_auth_post():
        username = request.forms.get('username')
        password = request.forms.get('password')
        try:
            allowed_commands, user_meta = PERMISSION_SERVICE.authenticate_user(
                username=username,
                password=password,
                empty_cache=True)
            group_swagger_link, output_file = associate_definition_with_group(
                username=username,
                swagger_path=swagger_path,
                available_commands=allowed_commands,
                prefix=CONFIG.prefix)

            api_doc(app,
                    config_path=output_file,
                    url_prefix=group_swagger_link,
                    title='Modular-API docs',
                    parameters=SWAGGER_SETTINGS)
            request.session[SWAGGER_ENABLED_KEY] = True
            SWAGGER_ALLOWED_PATH.append(group_swagger_link)
            return redirect(group_swagger_link)
        except ModularApiUnauthorizedException:
            return redirect('/swagger')


def secure_swagger_path(swagger_path):
    @hook('before_request')
    @tracer.wrap()
    def setup_request():
        request.session = request.environ['beaker.session']
        if request.path in SWAGGER_ALLOWED_PATH and not request.session.get(
                SWAGGER_ENABLED_KEY):
            redirect(swagger_path)


if __name__ == "__main__":
    app = default_app()
    try:
        host, port = _initialize()

        BaseRequest.MEMFILE_MAX = 5 * 1024 * 1024  # allow processing content
        # less than 5MB

        app_middleware = beaker.middleware.SessionMiddleware(app,
                                                             SESSION_SETTINGS)
        if CONFIG.swagger_ui_is_enabled:
            SWAGGER_PATH = CONFIG.prefix + SWAGGER_PATH
            swagger_login(swagger_path=SWAGGER_PATH)
            swagger_auth(swagger_path=SWAGGER_PATH)
            secure_swagger_path(swagger_path=SWAGGER_PATH)
        run(app_middleware, host=host, port=port)
    except Exception as e:
        exception_handler_formatter(
            logger=_LOG,
            exception=e,
            trace_id=None
        )
        raise ModularApiConfigurationException(e)
