import os
import pathlib
from base64 import b64decode

from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger(__name__)
TEMP_FILE_TEMPLATE = '.{0}_modular_temp'
SECURE_STRING = '*****'
TEMP_FILE_FOLDER_PATH = pathlib.Path(__file__).parent.parent.resolve()


def convert_param(param):
    return f'--{param}'


def build_param_and_value_in_click_format(param, value, secure_parameters,
                                          parameters_list,
                                          log_parameters_list):
    value_to_be_logged = value
    if param in secure_parameters:
        value_to_be_logged = SECURE_STRING
    param = convert_param(param)
    parameters_list.extend([param, value])
    log_parameters_list.extend([param, value_to_be_logged])
    return parameters_list, log_parameters_list


def is_valid_file_extensions_passed(meta_file_extensions,
                                    received_file_extension):
    if meta_file_extensions and (
            not received_file_extension or
            received_file_extension not in meta_file_extensions):
        raise ModularApiBadRequestException(
            f'File must have the following extensions: '
            f'{", ".join(meta_file_extensions)}')


def process_file_with_extension(file_extension: str, 
                                file_content: bytes, temp_file: str):
    with open(temp_file, 'wb') as file:
        file.write(file_content)


def convert_api_params(body, command_def, secure_parameters):
    """
    Convert api params and check
    :param body: The body of the request
    :param command_def: The command definition of the current
    command from command_base.json file
    :param secure_parameters: Secure parameters of the command
    :return: List of the temporary files
    """
    parameters_list = []
    log_parameters_list = []
    temp_files_list = []
    def_map = {j['name']: i for i, j in enumerate(command_def['parameters'])}
    for key, value in body.items():
        if def_map.get(key) and command_def['parameters'][def_map[key]].get(
                'convert_content_to_file'):

            meta_file_extensions = command_def['parameters'][def_map[key]].get(
                'temp_file_extension')
            received_file_extension = value['file_extension']
            is_valid_file_extensions_passed(
                meta_file_extensions=meta_file_extensions,
                received_file_extension=received_file_extension
            )

            temp_file_key = TEMP_FILE_TEMPLATE.format(key)
            temp_file = os.path.join(TEMP_FILE_FOLDER_PATH, temp_file_key)
            temp_file += received_file_extension

            process_file_with_extension(
                file_extension=received_file_extension,
                file_content=b64decode(value['file_content']),
                temp_file=temp_file
            )

            parameters_list, log_parameters_list = \
                build_param_and_value_in_click_format(
                    key, temp_file, secure_parameters, parameters_list,
                    log_parameters_list)

            temp_files_list.append(temp_file)
            continue

        is_flag = command_def['parameters'][def_map[key]].get('is_flag')
        if is_flag:
            if value not in [True, 'True', 'true']:
                raise ModularApiBadRequestException(
                    f'Unexpected value for the flag \'{key}\'. '
                    f'Only \'True\' is allowed, got \'{value}\'.'
                )
            pretty_param = convert_param(key)
            parameters_list.append(pretty_param)
            log_parameters_list.append(pretty_param)

        elif isinstance(value, (str, int, float, bool)):
            parameters_list, log_parameters_list = \
                build_param_and_value_in_click_format(
                    key, value, secure_parameters, parameters_list,
                    log_parameters_list)

        elif isinstance(value, list):
            for param_value in value:
                parameters_list, log_parameters_list = \
                    build_param_and_value_in_click_format(
                        key, param_value, secure_parameters, parameters_list,
                        log_parameters_list)

    return parameters_list, temp_files_list, log_parameters_list
