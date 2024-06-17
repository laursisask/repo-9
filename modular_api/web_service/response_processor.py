import urllib

from modular_api.helpers.exceptions import ModularApiInternalException, \
    ModularApiBadRequestException, ModularApiUnauthorizedException
from pynamodb.exceptions import GetError
from modular_api.helpers.log_helper import get_logger

M3MODULAR_ERROR_TYPE_KEY = 'error_type'
M3MODULAR_ERROR_MESSAGE_KEY = 'message'

_LOG = get_logger(__name__)


def build_exception_content(exception):
    if isinstance(exception, GetError) and getattr(
            exception, 'cause_response_code', '') == 'ExpiredTokenException':
        exception = ModularApiUnauthorizedException(
            'Token expired.')
    if not hasattr(exception, 'code'):
        exception = ModularApiInternalException('Exception occurred')
    code = exception.code
    error_type = exception.__class__.__name__
    error_message = str(exception)
    content = {
        M3MODULAR_ERROR_TYPE_KEY: error_type,
        M3MODULAR_ERROR_MESSAGE_KEY: error_message
    }
    return code, content


def __check_user_allowed_values(user_meta, requested_params):
    requested_params_names = requested_params.keys()
    for parameter in requested_params_names:
        if parameter in user_meta.keys():
            allow_list = [name.lower() for name in user_meta[parameter]
                          if isinstance(name, str)]
            user_value = requested_params[parameter].lower() \
                if isinstance(requested_params[parameter], str) \
                else requested_params[parameter]
            if user_value not in allow_list:
                invalid_requested_parameter_message = \
                    f'Invalid request for your user. Allowed value(s) ' \
                    f'for \'{parameter}\': {user_meta[parameter]}'
                _LOG.error(invalid_requested_parameter_message)
                raise ModularApiBadRequestException(
                    invalid_requested_parameter_message
                )


def validate_request(command, req_params, method, user_meta):
    if command['route']['method'] != method:
        raise ModularApiBadRequestException(
            f'The command {command["route"]["method"]} '
            f'is not available by method {method}')
    command_def_params = command['parameters']

    required_params = [param for param in command_def_params if
                       param['required']]
    all_param_names = [param['name'] for param in command_def_params]

    if len(all_param_names) == len(req_params) or len(req_params) > len(
            all_param_names):
        if not set(all_param_names) == set(req_params):
            wrong_parameters_specified_message = 'Wrong parameters specified'
            _LOG.error(wrong_parameters_specified_message)
            raise ModularApiBadRequestException(
                wrong_parameters_specified_message
            )
    else:
        required_params_names = [param['name'] for param in
                                 required_params]
        not_provided_params = set(required_params_names).difference(req_params)
        if not_provided_params:
            missed_params_error_message = \
                f'Not all required parameters specified: ' \
                f'{", ".join(not_provided_params)}'
            _LOG.error(missed_params_error_message)
            raise ModularApiBadRequestException(missed_params_error_message)
    __check_user_allowed_values(
        user_meta=user_meta,
        requested_params=req_params
    )
    return req_params


def extract_and_convert_parameters(request, command_def):
    result = {}
    if request.method == 'GET':
        query_string = request.query_string
        pairs = query_string.split('&')
        type_map = {item['name']: item['type']
                    for item in command_def['parameters']}
        for pair in pairs:
            split = pair.split('=')
            if len(split) == 2:
                param_name, param_value = split
                if '+' in param_value:
                    param_value = param_value.replace('+', ' ')
                value = urllib.parse.unquote(param_value)
                param = urllib.parse.unquote(param_name)
                result[param] = value
    else:
        result = {} if not request.json else request.json
    return result


def get_group_path(mount_point, group_name):
    if mount_point in ('/', group_name):
        return group_name
    return '/'.join([mount_point, group_name])
