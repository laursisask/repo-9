import json
import os
from datetime import datetime, timezone
from pathlib import Path
from itertools import chain

from modular_api.helpers.constants import LOG_FOLDER, ID, TIMESTAMP, KEY
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger(__name__)


class UsageHandler:
    def __init__(self, usage_service):
        self.usage_service = usage_service

    def get_stats_handler(self, from_month, to_month, display_table, path):
        _LOG.info(f'Going to get usage statistic. Parameters: from_month '
                  f'\'{from_month}\', to_month \'{to_month}\', '
                  f'display_table \'{display_table}\', path \'{path}\'')
        try:
            if from_month:
                fd_dt = datetime.strptime(from_month, '%Y-%m')
                from_date = int(fd_dt.timestamp()) * 1000
            else:
                utc_time_now = datetime.now(timezone.utc)
                utc_time_now = utc_time_now.replace(
                    day=1, hour=0, minute=0, second=0)
                from_date = int(utc_time_now.timestamp() * 1000)

            if to_month:
                td_dt = datetime.strptime(to_month, '%Y-%m')
                td_dt = td_dt.replace(day=1, hour=0, minute=0, second=0)
                to_date = int(td_dt.timestamp()) * 1000
            else:
                to_date = None
        except ValueError:
            _LOG.error('Invalid date format')
            raise ModularApiBadRequestException(
                'Please check date(s) spelling, required format is "yyyy-mm"')

        if (from_date and to_date) and (from_date >= to_date):
            _LOG.error('Invalid period')
            raise ModularApiBadRequestException(
                'Start month can not be greater than or equal to the end '
                'month')

        it = chain.from_iterable(
            self.usage_service.get_stats(key, from_date, to_date)
            for key in self.usage_service.modules_info
        )
        raw_result = [i.get_json() for i in it]

        if not raw_result:
            _LOG.info('No usage statistic by provided filters')
            return CommandResponse(
                message='There is no data by provided filters')

        table_report = self._prettify_report(raw_result, display_table)
        if table_report:
            return CommandResponse(table_title='Statistic', items=table_report)

        file_path = self._save_report_and_get_path(raw_result, path)
        _LOG.info(f'Report file has been stored by path: \'{file_path}\'')
        return CommandResponse(
            message=f'Report file has been stored by path: \'{file_path}\'')

    @staticmethod
    def _prettify_report(data, display_table) -> (list, None):
        if not display_table:
            return
        table_result = list()
        for item in data:
            item.pop(ID)
            item.pop(TIMESTAMP)
            table_result.append(item)
        return table_result

    @staticmethod
    def _save_report_and_get_path(data, path) -> str:
        if path:
            if not os.path.exists(path):
                _LOG.error(f'Provided path \'{path}\' does not exist')
                raise ModularApiBadRequestException(
                    f'Seems like path "{path}" does not exist. Please check '
                    f'spelling')
        else:
            pre_configured_user_dir = os.environ.get("M3MODULAR_USER_HOME")
            if pre_configured_user_dir:
                path = os.path.join(
                    pre_configured_user_dir, LOG_FOLDER, 'reports')
            else:
                path = os.path.join(
                    str(Path.home()), LOG_FOLDER, 'reports')
            if not os.path.exists(path):
                os.makedirs(path)

        tn = datetime.now(timezone.utc)
        file_name = f'{tn.day}-{tn.month}-{tn.year}-{tn.microsecond}.json'
        file_path = os.path.join(path, file_name)
        sorted_list = sorted(data, key=lambda d: d[TIMESTAMP])
        modified_list = list()
        for key, item in enumerate(sorted_list, start=1):
            item[KEY] = key
            modified_list.append(item)
        json_object = json.dumps(sorted_list, indent=4)
        try:
            with open(file_path, 'w') as file:
                file.write(json_object)
        except PermissionError:
            raise ModularApiBadRequestException(
                f'You do not have permissions to write files by path: '
                f'\'{path}\'')
        return file_path
