import json
from os import linesep
from datetime import datetime

import click

from modular_api.helpers.log_helper import get_logger
from modular_api.services.audit_service import AuditService
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.utilities import parse_date


_LOG = get_logger(__name__)


class AuditHandler:

    def __init__(self, audit_service):
        self.audit_service: AuditService = audit_service

    def describe_audit_handler(
            self,
            group: str | None = None,
            command: str | None = None,
            from_date: str | None = None,
            to_date: str | None = None,
            limit: int = 10,
            invalid: bool = False,
    ) -> CommandResponse:
        """
        Querying audit events by provided filters
        """
        _LOG.info(f'Describing audit events. Parameters: group \'{group}\', '
                  f'command \'{command}\', from_date \'{from_date}\', '
                  f'to_date \'{to_date}\', limit \'{limit}\', '
                  f'invalid \'{invalid}\'')
        if from_date:
            from_date = parse_date(from_date).replace(
                hour=0, minute=0, second=0, microsecond=0)
        if to_date:
            to_date = parse_date(to_date).replace(
                hour=23, minute=59, second=59, microsecond=0)
        if (from_date and to_date) and from_date >= to_date:
            message = 'The \'from_date\' parameter must not be greater ' \
                      'than or equal to the \'to_date\' parameter'
            _LOG.error(message)
            raise ModularApiBadRequestException(message)

        audit_list, invalid_list = self.audit_service.filter_audit(
            group=group, command=command, from_date=from_date,
            to_date=to_date, limit=limit)

        if invalid:
            if not invalid_list:
                _LOG.info('All events are valid')
                return CommandResponse(message='All events are valid')
            invalid_list.sort(key=lambda elem: elem.get('Timestamp'))
            file_name = self._save_file(invalid_list)
            if file_name:
                _LOG.info(f'Audit was successfully saved in: {file_name}')
                return CommandResponse(
                    message=f'Audit was successfully saved in: {file_name}')
            _LOG.warning('Invalid audit events detected')
            return CommandResponse(
                table_title='Invalid audit events', items=invalid_list)
        else:
            if not audit_list:
                _LOG.info('There are not events by provided filters')
                return CommandResponse(
                    message='There are not events by provided filters',
                    error=True,
                )
            audit_list.sort(key=lambda elem: elem.get('Timestamp'))
            file_name = self._save_file(audit_list)
            if file_name:
                _LOG.info(f'Audit was successfully saved in: {file_name}')
                return CommandResponse(
                    message=f'Audit was successfully saved in: {file_name}')
            valid_title = 'Audit events'
            compromised_title = f'Audit events{linesep}WARNING! ' \
                                f'Compromised event(s) have been detected.' \
                                f'{linesep}To view only invalid results ' \
                                f'use \'--invalid\' flag'
            _LOG.warning('Invalid audit events detected')

            return CommandResponse(
                table_title=valid_title if not invalid_list else compromised_title,
                items=audit_list,
            )

    @staticmethod
    def _save_file(items) -> str:
        """
        Writes audit events to the file and returns created file name
        """
        events_total = len(items)
        if events_total > 100 and click.confirm(
                text=f'Found {events_total} audit events. Do you want '
                     f'to save these records to a file??'):
            file_name = 'audit_' + datetime.utcnow(). \
                strftime("%d%m%Y_%H%M%S") + '.json'
            with open(file_name, 'w') as f:
                json.dump(items, f, indent=4)
            return file_name
