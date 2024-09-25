import json
import os
import sys
from copy import deepcopy
from functools import wraps

import click
from prettytable import PrettyTable

from modular_api.helpers.constants import CLI_VIEW, TABLE_VIEW, \
    MODULAR_API_RESPONSE, MAX_COLUMNS_WIDTH, JSON_VIEW

from modular_api.helpers.date_utils import utc_time_now
from modular_api.helpers.exceptions import ModularApiBaseException, \
    ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger, API_LOGS_FILE
from modular_api.services import SERVICE_PROVIDER

_LOG = get_logger(__name__)
new_line = os.linesep


class BaseCommand(click.core.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.insert(
            len(self.params),
            click.core.Option(
                ('--table',), is_flag=True,
                help='Use this parameter to show command`s response in a Table '
                     'view'
            )
        )
        self.params.insert(
            len(self.params),
            click.core.Option(
                ('--json',), is_flag=True,
                help='Use this parameter to show command`s response in a JSON '
                     'view'
            )
        )

    def main(self, *args, **kwargs):
        try:
            return super().main(*args, **kwargs)
        except Exception as e:
            raise ModularApiBaseException(str(e))


class ResponseDecorator:
    """
    Wrapper for formatting cli command response
    :param stdout: function which prints response to the end user
    :param error_message: message that will be displayed in case command
        failed to execute
    :return:
    """

    def __init__(self, stdout, error_message: str, custom_view: bool = False):
        self.stdout = stdout  # it's not stdout, it is a print function
        self.error_message = error_message
        self.custom_view = custom_view

    def __call__(self, fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            view_format = CLI_VIEW if self.custom_view else \
                resolve_output_format(kwargs=kwargs)
            try:
                resp = fn(*args, **kwargs)
            except ModularApiBaseException as context:
                _LOG.info('ModularApiBaseException occurred')
                resp = CommandResponse(message=str(context), error=True)
            except Exception:
                _LOG.exception('Unexpected exception occurred')
                message = f'Unexpected exception occurs.{os.linesep}' \
                          f'See detailed info and traceback in ' \
                          f'{API_LOGS_FILE}'
                resp = CommandResponse(message=message, error=True)
            func_result = ResponseFormatter(function_result=resp,
                                            view_format=view_format)
            response = self.stdout(func_result.prettify_response())
            if resp.error:
                sys.exit(1)
            return response
        return decorated


def resolve_output_format(kwargs):
    view_format = CLI_VIEW
    table_format = kwargs.pop(TABLE_VIEW, False)
    json_format = kwargs.pop(JSON_VIEW, False)
    if table_format and json_format:
        raise ModularApiBadRequestException(
            'Please specify only one parameter - table or json'
        )
    if table_format:
        view_format = TABLE_VIEW
    if json_format:
        view_format = JSON_VIEW
    return view_format


class ExceptionDecorator:
    """
    Wrapper for formatting only error response
    :param stdout: function which prints response to the end user
    :param error_message: message that will be displayed in case command
        failed to execute
    :return:
    """

    def __init__(self, stdout, error_message):
        self.stdout = stdout
        self.error_message = error_message

    def __call__(self, fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            view_format = resolve_output_format(kwargs=kwargs)
            try:
                return fn(*args, **kwargs)
            except ModularApiBaseException as context:
                _LOG.info('ModularApiBaseException occurred')
                resp = CommandResponse(message=str(context), error=True)
            except Exception:
                _LOG.exception('Unexpected exception occurred')
                message = f'Unexpected exception occurs.{os.linesep}' \
                          f'See detailed info and traceback in ' \
                          f'{API_LOGS_FILE}'
                resp = CommandResponse(message=message, error=True)

            func_result = ResponseFormatter(function_result=resp,
                                            view_format=view_format)
            self.stdout(func_result.prettify_response())
            exit()
        return decorated


class CommandResponse:
    def __init__(self, message: str = None, items: list = None,
                 warnings=None, table_title=None, error=False):
        self.error = error
        self.message = message
        self.warnings = [] if not warnings else warnings
        self.items = items
        self.table_title = table_title
        if not (self.table_title and self.items) and self.message is None:
            self.warnings.append(
                'Please provide "table_title", "items" or "message" parameter'
            )


class ResponseFormatter:
    def __init__(self, function_result, view_format):
        self.view_format = view_format
        self.function_result = function_result
        self.format_to_process_method = {
            CLI_VIEW: self.process_cli_view,
            TABLE_VIEW: self.process_table_view,
            JSON_VIEW: self.process_json_view,
        }

    @staticmethod
    def unpack_success_result_values(response_meta):
        warnings = response_meta.warnings
        message = response_meta.message
        items = response_meta.items
        table_title = response_meta.table_title
        return warnings, message, items, table_title

    def process_cli_view(self, response_meta):
        warnings, message, items, table_title = \
            self.unpack_success_result_values(response_meta=response_meta)
        if table_title and items:
            return self.process_table_view(response_meta=response_meta)
        if response_meta.error:
            return f'Error:{os.linesep}{message}'
        return message  # probably json, so we don't want to mangle it

    def process_table_view(self, response_meta: CommandResponse
                           ) -> PrettyTable:
        response = PrettyTable()

        warnings, message, items, table_title = \
            self.unpack_success_result_values(
                response_meta=response_meta)
        if message:
            response.field_names = [MODULAR_API_RESPONSE]
            response._max_width = {MODULAR_API_RESPONSE: 70}
            response.add_row([message])
        elif table_title and items:
            all_values = {}
            uniq_table_headers = []
            width_table_columns = {}
            for each_item in response_meta.items:
                if not isinstance(each_item, dict):
                    each_item = {'Result': each_item}
                for table_key, table_value in each_item.items():
                    if all_values.get(table_key):
                        all_values[table_key].append(table_value)
                    else:
                        all_values[table_key] = [table_value]
                    uniq_table_headers.extend([
                        table_key for table_key in each_item.keys()
                        if table_key not in uniq_table_headers
                    ])
                    if not width_table_columns.get(table_key) \
                            or width_table_columns.get(table_key) \
                            < len(str(table_value)):
                        width_table_columns[table_key] = len(str(table_value))
            import itertools
            response.field_names = uniq_table_headers
            response._max_width = {
                each: MAX_COLUMNS_WIDTH for each in uniq_table_headers
            }
            last_string_index = 0
            # Fills with an empty content absent items attributes to
            # align the table
            table_rows = itertools.zip_longest(
                *[j for i, j in all_values.items()], fillvalue='')
            for lst in table_rows:
                response.add_row(lst)
                row_separator = ['-' * min(
                    max(width_table_columns[uniq_table_headers[i]],
                        len(str(uniq_table_headers[i]))),
                    30) for i in range(len(uniq_table_headers))]
                response.add_row(row_separator)
                last_string_index += 2
            response.del_row(last_string_index - 1)

        response = (table_title + os.linesep if table_title else str()
                    ) + str(response)
        if response_meta.warnings:
            response += _prettify_warnings(response_meta.warnings)

        return response

    @staticmethod
    def process_json_view(response_meta: CommandResponse):
        json_view = response_meta.items
        if not json_view:
            json_view = {
                'status': 'error' if response_meta.error else 'success',
                'message': response_meta.message,
                'warnings': response_meta.warnings,
                'items': response_meta.items,
                'table_title': response_meta.table_title,
            }
            json_view = {
                k: v for k, v in json_view.items() if v
            }
        return json.dumps(json_view, indent=4)

    def prettify_response(self):
        view_processor = self.format_to_process_method[self.view_format]
        prettified_response = view_processor(response_meta=self.function_result)
        return prettified_response


def _prettify_warnings(warnings: list):
    return f'{os.linesep}WARNINGS:{os.linesep}' + \
           f'{os.linesep}'.join([str(i + 1) + '. ' + warnings[i]
                                 for i in range(len(warnings))])


def get_command_info(func):
    group = func.__module__.split(".")[-1]
    command = func.__name__
    return group, command


def produce_audit(secured_params=None):
    """
    Creates audit event and publishes after successful execution.
    :param secured_params: names of secured parameters - they won't be
        included to audit event.
    :return:
    """

    def real_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            group, command = get_command_info(func=func)
            parameters = deepcopy(kwargs)
            for param, value in kwargs.items():
                if secured_params and param in secured_params:
                    parameters[param] = '*****'
            try:
                func_result = func(*args, **kwargs)
            except ModularApiBaseException as e:
                raise e

            SERVICE_PROVIDER.audit_service.save_audit(
                group=group,
                command=command,
                timestamp=utc_time_now().isoformat(),
                parameters=json.dumps(parameters),
                result=func_result.message if func_result.message else str(func_result.items),
                warnings=func_result.warnings
            )

            return func_result
        return wrapper
    return real_wrapper
