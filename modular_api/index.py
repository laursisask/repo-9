import importlib.util
import json
import os
import sys
from http import HTTPStatus
from importlib.metadata import version as lib_version
from pathlib import Path
from unittest.mock import MagicMock
from dotenv import load_dotenv

import bottle
import click.exceptions
from bottle import request, Bottle, response
from ddtrace import tracer
from limits.storage import MongoDBStorage

from typing import Callable
from limits import RateLimitItemPerSecond, RateLimitItem
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter, RateLimiter
from modular_sdk.modular import Modular

from modular_api.commands_generator import (
    resolve_group_name, get_file_names_which_contains_admin_commands
)
from modular_api.helpers.compatibility_check import check_version_compatibility
from modular_api.helpers.constants import (
    MODULES_PATH, MODULE_NAME_KEY, EVENT_TYPE, META, AUX_DATA,
    PRODUCT, JOB_ID, STATUS, HTTPMethod, ServiceMode, COMMANDS_BASE_FILE_NAME,
    MODULAR_API_USERNAME, API_MODULE_FILE, MOUNT_POINT_KEY, SWAGGER_HTML
)
from modular_api.helpers.exceptions import (
    ModularApiUnauthorizedException, ModularApiBadRequestException
)
from modular_api.helpers.jwt_auth import (
    encode_data_to_jwt, username_from_jwt_token, decode_jwt_token
)
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.params_converter import convert_api_params
from modular_api.helpers.request_processor import generate_route_meta_mapping
from modular_api.helpers.response_processor import process_response
from modular_api.helpers.response_utils import get_trace_id, build_response
from modular_api.helpers.utilities import token_from_auth_header
from modular_api.services import SP
from modular_api.services.environment_service import EnvironmentService
from modular_api.services.permissions_cache_service import (
    permissions_handler_instance
)
from modular_api.swagger.generate_open_api_spec import generate_definition
from modular_api.version import __version__
from modular_api.web_service import META_VERSION_ID
from modular_api.web_service.config import Config
from modular_api.web_service.response_processor import (
    build_exception_content, validate_request, extract_and_convert_parameters,
    get_group_path
)

_LOG = get_logger(__name__)

MODULE_GROUP_GROUP_OBJECT_MAPPING = {}  # name to imported module
CONFIG = Config()  # currently keeps only commands_base.json
tracer.configure(writer=MagicMock())  # ???
WEB_SERVICE_PATH = os.path.dirname(__file__)
PERMISSION_SERVICE = permissions_handler_instance()
USAGE_SERVICE = SP.usage_service
THREAD_LOCAL_STORAGE = Modular().thread_local_storage_service()


def resolve_permissions(tracer, empty_cache=None):
    def decorator(func):
        def wrapper(*a, **ka):
            # sleep(0.35)  # for what?
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
            except Exception as e:
                _LOG.exception('Exception occurred resolving permissions')
                _trace_id = get_trace_id(tracer=tracer)
                # TODO sort out this trace id
                code, content = build_exception_content(exception=e)
                error_response = build_response(_trace_id=_trace_id,
                                                http_code=code,
                                                content=content)
                return error_response

        return wrapper

    return decorator


def get_module_group_and_associate_object() -> None:
    modules_path = Path(__file__).parent.resolve() / MODULES_PATH
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

            # todo what is this
            if is_private_group ^ SP.env.is_private_mode_enabled():
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


def initialize() -> None:
    """
    Can raise
    :return:
    """
    # loading configuration
    path = Path(__file__).parent / WEB_SERVICE_PATH / COMMANDS_BASE_FILE_NAME
    if os.path.exists(path):
        with open(path) as file:
            commands = json.load(file)
    else:
        commands = {}
    CONFIG.set_available_commands(available_commands=commands)
    _LOG.info('[init] Commands base phase completed')
    get_module_group_and_associate_object()


@tracer.wrap()
@resolve_permissions(tracer=tracer)
def web_help(allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    return build_response(
        _trace_id=_trace_id,
        http_code=HTTPStatus.OK,
        content={'available_commands': allowed_commands},
        message="This is the Modular-API administration tool. "
                "To request support, please contact "
                "Modular Support Team"
    )


@tracer.wrap()
@resolve_permissions(tracer=tracer)
def generate_group_or_command_help(path, allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)

    route_meta_mapping = generate_route_meta_mapping(
        commands_meta=allowed_commands)

    requested_command = []
    requested_commands = []
    for itinerary, command_meta in route_meta_mapping.items():
        if path in itinerary:  # todo, bug?
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
        http_code=HTTPStatus.OK,
        content={
            'available_commands': requested_command or requested_commands},
        message="This is the Modular-API administration tool. "
                "To request support, please contact "
                "Modular Support Team"
    )


def __validate_cli_version(_trace_id):
    try:
        version_warnings = check_version_compatibility(
            min_allowed_version=SP.env.min_cli_version(),
            current_version=request.headers.get('Cli-Version')
        )
        return version_warnings, None
    except ModularApiBadRequestException as e:
        _LOG.warning('Version compatibility checker failed', exc_info=True)

        code, content = build_exception_content(exception=e)
        error_response = build_response(_trace_id=_trace_id,
                                        http_code=code,
                                        content=content)
        return None, error_response


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
        'version': __version__
    }
    if meta_return:
        add_versions_to_allowed_modules(allowed_commands)
        data['meta'] = allowed_commands
    if version_warning:
        data['warnings'] = version_warning

    return build_response(_trace_id=_trace_id, http_code=HTTPStatus.OK,
                          content=data)


def add_versions_to_allowed_modules(allowed_commands: dict) -> None:
    """
    Changes the given dict in place
    :param allowed_commands:
    :return: None
    """
    # todo refactor with resolve_user_available_components_version ASAP

    for module in (Path(__file__).parent / MODULES_PATH).iterdir():
        api_file_path = module / API_MODULE_FILE
        if not module.is_dir() or not api_file_path.exists():
            continue
        with open(api_file_path, 'r') as file:
            module_descriptor = json.load(file)

        mount_point = module_descriptor[MOUNT_POINT_KEY]
        if mount_point in allowed_commands:
            allowed_commands[mount_point]['version'] = lib_version(
                module_descriptor[MODULE_NAME_KEY])


def resolve_user_available_components_version(allowed_commands: dict):
    modules_path = Path(__file__).parent / MODULES_PATH
    components_versions = {}
    for module in modules_path.iterdir():
        api_file_path = module / API_MODULE_FILE
        if not module.is_dir() or not api_file_path.exists():
            continue
        with open(api_file_path, 'r') as file:
            module_descriptor = json.load(file)
        if module_descriptor[MOUNT_POINT_KEY] in allowed_commands:
            module_name = module_descriptor[MODULE_NAME_KEY]
            components_versions[module_name] = lib_version(module_name)
    return components_versions


@tracer.wrap()
@resolve_permissions(tracer=tracer, empty_cache=False)
def version(allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    resolve_user_available_components_version(allowed_commands)
    data = {'modular_api': __version__}
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
        http_code=HTTPStatus.OK,
        content=response_template
    )


@tracer.wrap()
def health_check():
    _trace_id = get_trace_id(tracer=tracer)
    return build_response(
        _trace_id=_trace_id,
        http_code=HTTPStatus.OK,
        content=None
    )


@tracer.wrap()
@resolve_permissions(tracer=tracer, empty_cache=True)
def stats(allowed_commands, user_meta):
    _trace_id = get_trace_id(tracer=tracer)
    entry_request = request
    required_params = [EVENT_TYPE, PRODUCT, JOB_ID, STATUS, META]

    absent_params = [param for param in required_params
                     if not entry_request.json.get(param)]
    if absent_params:
        return build_response(
            _trace_id=_trace_id,
            http_code=HTTPStatus.BAD_REQUEST,
            content=None
        )

    payload = {param: entry_request.json.get(param)
               for param in required_params}

    USAGE_SERVICE.save_stats(request=entry_request, payload=payload)
    return build_response(_trace_id=_trace_id, content=None)


def __automated_relogin(request_item) -> bool:
    header = request_item.headers.get('Authorization')
    raw_token = header.split(maxsplit=2)[-1]
    token = decode_jwt_token(raw_token)
    client_meta_version = token.get('meta_version')
    if client_meta_version == META_VERSION_ID:
        return False
    return True


def swagger_html():
    response.content_type = 'text/html'
    return SWAGGER_HTML.format(
        version='latest',
        url=request.app.get_url('swagger-spec')
    )


def swagger_spec():
    route_meta_mapping = generate_route_meta_mapping(
        commands_meta=CONFIG.available_commands
    )
    response.content_type = 'application/json'
    return generate_definition(
        commands_def=route_meta_mapping,
        prefix=request.fullpath[:-len(request.path)]  # todo, maybe won't work in some sophisticated situations but for our case ok
    )


@tracer.wrap()
@resolve_permissions(tracer=tracer)
def index(path: str, allowed_commands=None, user_meta=None):
    _trace_id = get_trace_id(tracer=tracer)
    temp_files_list = []
    try:
        # TODO sort out relogin and remove
        relogin_needed = __automated_relogin(request)
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

        method = request.method

        route_meta_mapping = generate_route_meta_mapping(
            commands_meta=allowed_commands)

        command_def = route_meta_mapping.get(path)
        if not command_def:
            raise ModularApiBadRequestException('Can not found requested '
                                                'command')
        request_body_raw = extract_and_convert_parameters(
            request=request,
            command_def=command_def
        )

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
        if not username:
            username, _ = request.auth
        # saving username to thread-local storage
        THREAD_LOCAL_STORAGE.set('modular_user', username)
        curr_user = SP.user_service.describe_user(username)
        # saving the meta.aux_data of user in the thread-local storage
        modular_user_meta_aux = {}
        if curr_user.meta:
            meta_dict = curr_user.meta.as_dict()
            aux_data = meta_dict.get(AUX_DATA)
            modular_user_meta_aux = (
                aux_data if isinstance(aux_data, dict) else {}
            )
        THREAD_LOCAL_STORAGE.set('modular_user_meta_aux', modular_user_meta_aux)

        # hopefully, token will be here... otherwise 500, I mean, it must be
        # here because the endpoint is authorized by token
        try:
            response = correct_method.main(
                args=parameters,
                standalone_mode=False,
                obj={MODULAR_API_USERNAME: username}
            )
        except click.exceptions.UsageError as error:
            # just in case something is not handled
            return build_response(
                _trace_id=_trace_id,
                http_code=200,  # means that click worked,
                message=str(error)
            )
        # obj goes to click.Context. Other module CLI should use it to
        # understand what user is making the request
        response = json.loads(response)
        _LOG.info(f'Obtained response {response} for {_trace_id} request')
        content, code = process_response(response=response)
        payload = {key.lower(): value for key, value in response.items()}
        USAGE_SERVICE.save_stats(request=request, payload=payload)  # TODO raises Value error sometimes
        if content.get('warnings'):
            if version_warning:
                content['warnings'].extend(version_warning)
        else:
            content['warnings'] = version_warning
        return build_response(_trace_id=_trace_id,
                              http_code=code,
                              content=content)

    except Exception as e:
        # TODO use _LOG.exception
        _LOG.exception('Unexpected exception occurred')
        code, content = build_exception_content(exception=e)
        error_response = build_response(_trace_id=_trace_id,
                                        http_code=code,
                                        content=content)
        USAGE_SERVICE.save_stats(request=request, payload=content)
        return error_response
    finally:  # todo what temp files?, for what? since they are temp files, why should we remove them?
        if temp_files_list:
            for each_file in temp_files_list:
                os.remove(each_file)


class RateLimitMiddleware:
    __slots__ = 'app', 'limiter', 'limit'

    def __init__(self, app: Callable, limiter: RateLimiter,
                 limit: RateLimitItem):
        self.app = app
        self.limiter = limiter
        self.limit = limit

    def __call__(self, environ, start_response):
        if not self.limiter.hit(self.limit, environ.get('REMOTE_ADDR')):
            _LOG.debug('Requests limit hit. Returning 429')
            c = HTTPStatus.TOO_MANY_REQUESTS
            start_response(
                f'{c.value} {c.phrase}', [('Content-Type', 'text/plain')],
            )
            return [HTTPStatus.TOO_MANY_REQUESTS.description.encode()]
        return self.app(environ, start_response)


class WSGIApplicationBuilder:
    def __init__(self, env: EnvironmentService, prefix: str = '',
                 swagger: bool = False, swagger_prefix: str = '/swagger'):
        self._env = env
        self._prefix = prefix
        self._swagger = swagger
        self._swagger_prefix = swagger_prefix

    @staticmethod
    def _build_generic_error_handler(code: HTTPStatus) -> Callable:
        """
        Builds a generic callback that handles a specific error code
        :param code:
        :return:
        """
        def f(error):
            return json.dumps({'message': code.phrase}, separators=(',', ':'))
        return f

    def _register_errors(self, application: Bottle) -> None:
        to_handle = (HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR)
        for code in to_handle:
            application.error_handler[code.value] = self._build_generic_error_handler(code)

    def _rate_limited(self, app: Callable) -> Callable:
        match self._env.mode():
            case ServiceMode.SAAS:
                storage = MemoryStorage()
                # todo fix for saas, either implement storage for dynamodb
                #  or move completely to mongo, or use redis just for broker
                #  or use nginx and set rate limiting there.
                #  This MemoryStorage performs far from perfect when multiple
                #  processes and should not be used
            case _:
                storage = MongoDBStorage(
                    uri=self._env.mongo_uri(),
                    database_name=self._env.mongo_rate_limits_database()
                )
        return RateLimitMiddleware(
            app=app,
            limiter=MovingWindowRateLimiter(storage),
            limit=RateLimitItemPerSecond(self._env.api_calls_per_second_limit())
        )

    def build(self) -> Callable:
        """
        It returns a wsgi callable, not a Bottle instance
        :return:
        """
        _LOG.info('Building WSGI application')
        child = Bottle()
        self._register_errors(child)
        if self._swagger:
            child.route(
                path='/swagger.json',
                method=HTTPMethod.GET,
                callback=swagger_spec,
                name='swagger-spec'
            )
            child.route(
                path=self._swagger_prefix,
                method=HTTPMethod.GET,
                callback=swagger_html
            )

        child.route(
            path='/doc',
            method=HTTPMethod.GET,
            callback=web_help
        )
        child.route(
            path='/doc<path:path>',
            method=HTTPMethod.GET,
            callback=generate_group_or_command_help
        )
        child.route(
            path='/login',
            method=HTTPMethod.GET,
            callback=login
        )
        child.route(
            path='/version',
            method=HTTPMethod.GET,
            callback=version
        )
        child.route(
            path='/health_check',
            method=HTTPMethod.GET,
            callback=health_check
        )

        child.route(
            path='/stats',
            method=HTTPMethod.POST,
            callback=stats
        )
        # TODO use some prefix for all commands, because this catches
        #  everything
        child.route(
            path='<path:path>',
            method=[HTTPMethod.POST, HTTPMethod.GET],
            callback=index
        )

        if self._prefix:
            application = Bottle()
            self._register_errors(application)
            pr = f'/{self._prefix.strip("/")}/'
            application.mount(pr, child)
        else:
            application = child

        application = self._rate_limited(application)
        _LOG.info('WSGI application was built')
        return application


def main():
    load_dotenv(verbose=True)
    sys.stderr.write(
        '[WARNING] This way to start the server is deprecated and '
        'will be removed. Please, use "modular run" command instead\n'
    )
    # warnings.warn(DeprecationWarning(
    #     'This way to start the server is deprecated and '
    #     'will be removed. Please, use "modular run" command instead'
    # ))
    initialize()  # can raise
    application = WSGIApplicationBuilder(SP.env).build()
    bottle.run(application, host='127.0.0.1', port=8085)


if __name__ == "__main__":
    main()
