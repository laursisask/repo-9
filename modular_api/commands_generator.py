import copy
import importlib
import inspect
import os
import re
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

from click import Group
from click.types import Choice, IntRange, FloatRange

from modular_api.helpers.log_helper import get_logger

ALLOWED_EXTENSIONS_PATTERN = r"(?<=allowed_extensions=\[)['., \w]+(?=])"

GROUP_NAME_SEPARATOR = '_'
DEFAULT_METHOD = 'POST'

_LOG = get_logger(__name__)


FILE_CHECKS_CALLBACKS = ['callback=check_path_exists_required',
                         'callback=check_path_exists_optional',
                         'callback=check_file_exists_required',
                         'callback=validate_file_required',
                         'callback=validate_file_optional',
                         'callback=create_file_if_it_not_exists']

REQUIRED_PARAM_CALLBACKS = ['required=True',
                            'check_required_param',
                            'check_required_param_and_to_lower',
                            'verify_required_email',
                            'verify_required_email_and_to_lower',
                            'check_required_list_and_convert_in_upper_case',
                            'check_required_param_and_convert_in_upper_case',
                            'check_param_by_regex_required',
                            'check_path_exists_required',
                            'check_file_exists_required',
                            'check_is_digit_required',
                            'parse_date_and_convert_to_timestamp_required',
                            'parse_date_required',
                            'parse_date_yyyy_mm',
                            'parse_date_yyyy_mm_dd_hh',
                            'validate_file_required']

DICT_WITH_CREDS_FOR_MOCK = {
    'Arn': 'user/asdfasdf',
    'Credentials': {
        'SecretAccessKey': 'mock',
        'AccessKeyId': 'mock',
        'SessionToken': 'mock',
        'Expiration': datetime.utcnow() + timedelta(seconds=10)
    }
}


def resolve_group_name(group_file):
    file_name_wo_ext = group_file.split('.')[0]
    group_full_name_list = __resolve_group_name(
        file_name_wo_ext)
    group_name = group_full_name_list[-1] if type(
        group_full_name_list) == list else group_full_name_list
    return group_full_name_list, group_name


def get_file_names_which_contains_admin_commands(path_to_scan):
    listdir = [filename for filename in os.listdir(path_to_scan)
               if filename.endswith('.py') and not filename.startswith('_')]
    return listdir


def _resolve_root_group_name(file_content):
    root_group_name = None
    for idx, line in enumerate(file_content):
        if 'project.scripts' in line or 'console_scripts' in line:
            root_file_path = file_content[idx + 1]
            root_group_name = re.findall(r"(?<=\.)[^.:\s]+(?=:)", root_file_path)
    if not root_group_name:
        raise AssertionError('Can not resolve root group name')
    return root_group_name[0]


def generate_valid_commands(destination_folder,
                            path_to_setup_file_in_module,
                            path_to_scan=None,
                            mount_point='',
                            is_private_mode_enabled=False):
    # generate or compute the path to process
    _LOG.info(f'[commands] Path to scan: {path_to_scan}')

    # iterate files
    valid_methods = {'type': 'module', 'body': {}}
    listdir = get_file_names_which_contains_admin_commands(
        path_to_scan=path_to_scan)

    if destination_folder not in sys.path:
        sys.path.append(destination_folder)

    with open(path_to_setup_file_in_module) as file:
        file_content = file.readlines()

    root_group_name = _resolve_root_group_name(file_content=file_content)

    for group_file in sorted(listdir):
        group_full_name_list, group_name = resolve_group_name(
            group_file=group_file)
        is_private_group = (isinstance(group_full_name_list, list) and
                            group_full_name_list[0] == 'private' or
                            group_full_name_list == 'private')

        is_subgroup = (isinstance(group_full_name_list, list) and
                       not is_private_group)
        is_root_group = root_group_name == group_name
        if is_private_group ^ is_private_mode_enabled:
            continue

        # from index.py -> get_module_group_and_associate_object
        module_spec = importlib.util.spec_from_file_location(
            group_name,
            os.path.join(path_to_scan, group_file))
        imported_module = importlib.util.module_from_spec(module_spec)
        with patch('botocore.client.BaseClient._make_api_call',
                   return_value=DICT_WITH_CREDS_FOR_MOCK):
            module_spec.loader.exec_module(imported_module)
        commands = CommandsDefinitionsExtractor(group_name,
                                                imported_module,
                                                mount_point).extract(subgroup=is_subgroup)
        group_meta = {"type": "group", 'body': commands}
        if is_subgroup:
            if not valid_methods['body'].get(group_full_name_list[0]):
                valid_methods['body'][group_full_name_list[0]] = {'body': {}}
            if isinstance(group_full_name_list, list) \
                    and len(group_full_name_list) > 2:
                if not valid_methods['body'][group_full_name_list[0]]['body'].get(group_full_name_list[1]):
                    valid_methods['body'][group_full_name_list[0]]['body'][group_full_name_list[1]] = {'body': {}}
                # todo refactor this
                valid_methods['body'][group_full_name_list[0]]['body'][group_full_name_list[1]]['body'].update(
                    {group_name: group_meta})
            else:
                valid_methods['body'][group_full_name_list[0]]['body'].update(
                    {group_name: group_meta})
        elif is_root_group:
            root_commands_meta = group_meta.pop('body')
            for root_command_meta in root_commands_meta.values():
                root_command_meta['type'] = 'root command'
            valid_methods['body'].update(root_commands_meta)
        else:
            valid_methods['body'][group_name] = group_meta
    if destination_folder in sys.path:
        sys.path.remove(destination_folder)
    return valid_methods


def __resolve_group_name(group_filename):
    if GROUP_NAME_SEPARATOR not in group_filename:
        return group_filename
    return group_filename.split(GROUP_NAME_SEPARATOR)


def _get_param_def_from_line(line):
    if '\'\'' in line:
        line = line.replace('\'\'', '')
    split = [line for line in line.split('\'') if line]
    param_name = None
    param_doc = None
    alias_name = None
    param_type = 'str'
    is_flag = False
    is_path_to_file = False
    file_extension = None
    for index, part in enumerate(split):
        # todo this all does not seem right...
        if any(i in part for i in FILE_CHECKS_CALLBACKS):
            is_path_to_file = True
            match = re.search(ALLOWED_EXTENSIONS_PATTERN, line)
            if match:
                allowed_extensions = match.group().split(', ')
                file_extension = [extension.strip("\"'")
                                  for extension in allowed_extensions]
        if re.match(r'^--[a-z]', part):
            param_name = str(part).replace('--', '')
        if re.match(r'^-[a-zA-z]', part):
            alias_name = str(part).replace('-', '')
        if 'help=' in part:
            param_doc = str(split[index + 1])
            param_doc = param_doc.replace('*', '').strip() \
                if '*' in param_doc \
                else param_doc
        if 'is_flag' in part:
            param_type = 'bool'
            is_flag = True
        if 'type' in part:
            click_type = part.split('type=', 1)[-1].split(',')[0]
            if 'Choice' in click_type:
                click_type = 'enum'
            if 'IntRange' in click_type or 'float' in click_type:
                click_type = 'num'
            if click_type not in ['list', 'str', 'bool', 'enum', 'num']:
                click_type = 'str'
            param_type = click_type
            if 'multiple' in part:
                param_type = 'list'

    param_required = any(i in line for i in REQUIRED_PARAM_CALLBACKS)
    response = {
        'name': param_name,
        'alias': alias_name,
        'required': param_required,
        'description': param_doc,
        'type': param_type,
        'is_flag': is_flag
    }
    if is_path_to_file:
        response['convert_content_to_file'] = is_path_to_file
    if file_extension:
        response['temp_file_extension'] = file_extension
    return response


class CommandsDefinitionsExtractor:
    DEFAULT_METHOD = 'POST'
    DEFAULT_MOUNT_POINT = '/'
    click_to_our_types_mapping = {
        'choice': 'enum',
        'boolean': 'bool',
        'text': 'str',
        'integer': 'str'
    }

    def __init__(self, group_name, module, mount_point=DEFAULT_MOUNT_POINT):
        self._group_name = group_name
        self._module = module
        self._mount_point = mount_point
        self._Command = getattr(
            importlib.import_module('click.core'), 'Command'
        )

    @staticmethod
    def _get_alias(opts):
        """Get alias from click's opts. They look like ['--param', '-p'].
        Trere are no guarantee that alias will be second."""
        if len(opts) == 1:
            return None
        for opt in opts:
            if opt[1] != '-':
                return opt[1:]

    @staticmethod
    def _merge_route_configs(primary, secondary):
        for node in secondary:
            if primary.get(node):
                secondary[node] = primary.get(node)
        return secondary

    def _get_default_route_config(self, group_full_name, command_name, subgroup):
        full_group_path = '/'.join(group_full_name) \
            if isinstance(group_full_name, list) else group_full_name
        if subgroup:
            module_path = str(self._module)
            resolved_parents = re.search('\w*.(?=.py)', module_path).group(0)
            path_components = resolved_parents.split('_')
            subgroup_path = '/'.join(component for component in path_components)
            path = f'/{subgroup_path}/{command_name}' \
                if self._mount_point == '/' \
                else f'{self._mount_point}/{subgroup_path}/{command_name}'
        else:
            path = f'/{full_group_path}/{command_name}' \
                if self._mount_point == '/' \
                else f'{self._mount_point}/{full_group_path}/{command_name}'
        return {
            'method': self.DEFAULT_METHOD,
            'path': path
        }

    @staticmethod
    def _get_route_configuration_from_line(line, default):
        default_route = {'method': 'GET'}
        if '=' not in line:
            return default_route

        line = line.replace('\'', '')
        start_index = line.index('(')
        end_index = line.index(')')
        line = line[start_index + 1: end_index]  #
        parameters = line.split(',')
        for parameter_def in parameters:
            split = parameter_def.split('=')
            name = split[0].strip()
            value = split[1].strip()
            default_route[name] = value
        return default_route

    @staticmethod
    def _get_parameters_to_be_secured(line):
        parameters_to_be_secured = []

        line = line.replace('\'', '')
        start_index = line.index('[')
        end_index = line.index(']')
        line = line[start_index + 1: end_index]
        parameters = line.split(',')

        for parameter in parameters:
            parameters_to_be_secured.append(parameter.strip())

        return parameters_to_be_secured

    def _get_api_route_flag_and_secured_params(self, subgroup):
        group_content = inspect.getsource(self._module)
        lines = group_content.split('\n')
        command_definitions = {}
        for index, line in enumerate(lines):
            if line.startswith('#'):
                continue
            if '@{}.command'.format(self._group_name) in line:
                # find from @{group}.command to enclosing  """ of docstring
                command_lines = [line]
                comment_close_sum_counter = 0
                counter = 1
                # definition of command function
                command_def_line_passed = False
                while comment_close_sum_counter != 2:
                    current_line = lines[index + counter]
                    if 'def ' in current_line:
                        command_def_line_passed = True
                    if command_def_line_passed and '):' in current_line and \
                            '\"\"\"' not in lines[index + counter + 1]:
                        comment_close_sum_counter = 2  # to break the loop
                    if '\"\"\"' in current_line:
                        comment_close_sum_counter += 1
                        counter += 1
                        continue

                    command_lines.append(current_line.strip())
                    counter += 1
                # prepare for analysis
                prepared_lines = []
                for i, line in enumerate(command_lines):
                    if not str(line).startswith('@') and not \
                            str(line).startswith('def'):
                        prepared_lines[-1] = prepared_lines[-1] + line
                    else:
                        prepared_lines.append(line)

                # analyze lines
                name = None
                is_command_hidden = False
                route_config = {}
                secure_parameters = []
                files_parameters = {}
                security_parameters_found = False
                secured_parameters_string = ''
                flag_parameters = []
                for line in prepared_lines:
                    if f'@{self._group_name}.command' in line:
                        name = line.split('\'')[1]
                    if '@api_route' in line:
                        route_config = self._get_route_configuration_from_line(
                            line=line, default=route_config)
                    if '@click.option' in line:
                        response = _get_param_def_from_line(line)
                        param_name = response.get('name')
                        if response.get('is_flag'):
                            flag_parameters.append(param_name)
                        convert_content_to_file = response.get('convert_content_to_file')
                        temp_file_extension = response.get('temp_file_extension')
                        if any([convert_content_to_file, temp_file_extension]):
                            files_parameters.update(
                                {
                                    param_name: {
                                        'convert_content_to_file': convert_content_to_file,
                                        'temp_file_extension': temp_file_extension
                                    }
                                }
                            )
                    if '@shadow_wrapper' in line:
                        is_command_hidden = True
                    if 'secured_params=' in line \
                            and not security_parameters_found:
                        if ']' in line:
                            security_parameters_found = True
                            secured_parameters_string += line
                            secure_parameters = self._get_parameters_to_be_secured(
                                secured_parameters_string)
                        secured_parameters_string += line

                default_rt = self._get_default_route_config(
                    group_full_name=self._group_name,
                    command_name=name,
                    subgroup=subgroup
                )
                route_config = self._merge_route_configs(primary=route_config,
                                                         secondary=default_rt)

                command_definitions.update({
                    name: {
                        'route': route_config,
                        'secure_parameters': secure_parameters,
                        'files_parameters': files_parameters,
                        'is_command_hidden': is_command_hidden,
                        'flag_parameters': flag_parameters
                    }
                })
        return command_definitions

    def extract(self, subgroup):
        definitions = {}
        for entity in dir(self._module):
            click_command = getattr(self._module, entity)
            if not isinstance(click_command, self._Command) or \
                    click_command.name == self._group_name or \
                    isinstance(click_command, Group):
                continue
            parameters = []
            for param in click_command.params:
                required = (param.callback and param.callback.__name__
                            in REQUIRED_PARAM_CALLBACKS) or param.required
                param_help = param.help.replace('* ', '') if param.help else ''
                param_meta = {
                    'name': param.human_readable_name,
                    'alias': self._get_alias(param.opts),
                    'required': required,
                    'description': param_help,
                    'type': self.click_to_our_types_mapping.get(
                        param.type.name, param.type.name)
                }
                if isinstance(param.type, (Choice)):
                    # TODO refactor asap
                    choices = param.type.choices
                    param_meta['description'] += f' {"|".join(choices)}'
                if isinstance(param.type, (IntRange, FloatRange)):
                    # TODO update click and use get_metavar
                    param_meta['description'] += f' {param.type.min or ""}<=x<={param.type.max or ""}'
                parameters.append(param_meta)
            definitions.update({
                click_command.name: {
                    'body': {
                        'description': click_command.help,
                        'parameters': parameters,
                        'handler': entity,
                        'parent': self._group_name
                    }
                }
            })
        routes_and_secured_params = (
            self._get_api_route_flag_and_secured_params(subgroup))
        for name, body in definitions.items():
            command_config = routes_and_secured_params.get(name, {})
            files_parameters = command_config.pop('files_parameters', None)
            if files_parameters:
                command_params = body['body']['parameters']
                for param in command_params:
                    param_name = param.get('name')
                    if param_name in files_parameters:
                        param.update(files_parameters[param_name])
            body['body'].update(routes_and_secured_params.get(name, {}))

        definitions_copy = copy.deepcopy(definitions)
        for name, body in definitions.items():
            command_config = routes_and_secured_params.get(name, {})
            flag_parameters = command_config.get('flag_parameters')
            if flag_parameters:
                for idx, param in enumerate(body['body']['parameters']):
                    if param['name'] in flag_parameters:
                        definitions_copy[name]['body']['parameters'][idx][
                            'is_flag'] = True
            definitions_copy[name]['body'].pop('flag_parameters', None)
            is_command_hidden = command_config.pop('is_command_hidden', None)
            if is_command_hidden:
                definitions_copy.pop(name)
        return definitions_copy
