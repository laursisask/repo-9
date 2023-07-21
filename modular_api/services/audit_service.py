import json

from pynamodb.pagination import ResultIterator

from modular_api.models.audit_model import Audit
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string
from datetime import datetime, timedelta

SAAS_MODE = 'saas'
AUDIT_TIME_TMPL = '%d.%m.%Y %H:%M:%S'
_LOG = get_logger('audit_service')


class AuditService:

    @staticmethod
    def prepare_audit_to_be_hashed(audit: Audit) -> dict:
        _LOG.info(f'Going to prepare audit to be hashed')
        """
        Returns audit event as dictionary from Audit table without hash
        attribute. All values in dictionary are string type
        """
        audit = audit.response_object_without_hash()
        audit['timestamp'] = audit.get('timestamp').strftime(
            "%d.%m.%Y %H:%M:%S")
        return audit

    def save_audit(self, timestamp, group, command, parameters,
                   result, warnings=None) -> None:
        _LOG.info(f'Going to save audit')
        """
        Saves event and its hash sum to the 'ModularAudit' table
        """
        audit = Audit(group=group, timestamp=timestamp, command=command,
                      parameters=parameters, result=result, warnings=warnings)

        event_to_be_hashed = self.prepare_audit_to_be_hashed(audit=audit)
        event_to_be_hashed = json.dumps(event_to_be_hashed)
        audit.hash_sum = secure_string(event_to_be_hashed)
        audit.save()

    @staticmethod
    def check_audit_hash(audit: Audit) -> bool:
        """
        Compares an existing audit event with its hash sum
        """
        _LOG.info(f'Going to check audit hash')
        audit_hash = audit.hash_sum
        if not audit_hash:
            return False
        provided_audit = AuditService.prepare_audit_to_be_hashed(audit=audit)
        provided_audit = secure_string(json.dumps(provided_audit))
        return provided_audit == audit_hash

    @staticmethod
    def get_audit(group, command, from_date, to_date, limit) -> ResultIterator:
        """
        Returns iterator with filtered results
        """
        filter_condition = None
        range_key_condition = None

        if from_date and to_date:
            range_key_condition &= (
                Audit.timestamp.between(from_date, to_date))
        elif from_date:
            range_key_condition &= (Audit.timestamp >= from_date)
        elif to_date:
            range_key_condition &= (Audit.timestamp <= to_date)
        else:
            initial_date = datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
            range_key_condition &= (Audit.timestamp >= initial_date)

        if command:
            filter_condition &= (Audit.command == command)

        if group:
            return Audit.query(hash_key=group,
                               filter_condition=filter_condition,
                               range_key_condition=range_key_condition,
                               limit=limit)

        if range_key_condition is not None:
            filter_condition &= range_key_condition

        return Audit.scan(filter_condition=filter_condition)

    def filter_audit(self, group=None, from_date=None, to_date=None,
                     command=None, limit=None) -> tuple:
        """
        Returns audit events by provided filters
        """
        _LOG.info(f'Going to filter audit by the following parameters: group: '
                  f'{group}, command: {command}, from_date: {from_date}, '
                  f'to_date: {to_date}, limit: {limit}')

        audit_list = []
        invalid_list = []

        audit = self.get_audit(group=group, command=command,
                               from_date=from_date,
                               to_date=to_date, limit=limit)

        for event in audit:
            valid_event = AuditService.check_audit_hash(event)
            pretty_value = {
                'Group': event.group,
                'Command': event.command,
                'Timestamp': event.timestamp.strftime(AUDIT_TIME_TMPL),
                'Parameters': event.parameters,
                'Execution warnings': event.warnings,
                'Result': event.result,
                'Consistency status': 'Compromised' if not valid_event else 'OK'
            }
            if not valid_event:
                invalid_list.append(pretty_value)
            audit_list.append(pretty_value)
        return audit_list, invalid_list
