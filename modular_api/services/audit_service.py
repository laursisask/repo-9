import json

from pynamodb.pagination import ResultIterator

from modular_api.models.audit_model import Audit
from modular_api.helpers.date_utils import convert_datetime_to_human_readable
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string
from datetime import datetime, timedelta

_LOG = get_logger(__name__)


class AuditService:

    @staticmethod
    def prepare_audit_to_be_hashed(audit: Audit) -> dict:
        """
        Returns audit event as dictionary from Audit table without hash
        attribute. All values in dictionary are string type
        """
        _LOG.info(f'Preparing audit event to be hashed')
        return audit.response_object_without_hash()

    def save_audit(self, timestamp: str, group: str, command: str,
                   parameters: str,
                   result: str, warnings=None) -> None:
        """
        Saves event and its hash sum to the 'ModularAudit' table
        """
        _LOG.info(f'Saving audit item')
        audit = Audit(group=group, timestamp=timestamp, command=command,
                      parameters=parameters, result=result, warnings=warnings)
        event_to_be_hashed = self.prepare_audit_to_be_hashed(audit=audit)
        event_to_be_hashed = json.dumps(event_to_be_hashed, sort_keys=True)
        audit.hash_sum = secure_string(event_to_be_hashed)
        audit.save()

    @staticmethod
    def check_audit_hash(audit: Audit) -> bool:
        """
        Compares an existing audit event with its hash sum
        """
        _LOG.info(f'Checking audit event hash')
        audit_hash = audit.hash_sum
        if not audit_hash:
            return False
        provided_audit = AuditService.prepare_audit_to_be_hashed(audit=audit)
        provided_audit = secure_string(json.dumps(provided_audit))
        return provided_audit == audit_hash

    @staticmethod
    def get_audit(group, command, from_date, to_date, limit
                  ) -> ResultIterator[Audit]:
        """
        Returns iterator with filtered results
        """
        _LOG.info('Describing audit table')
        filter_condition = None
        range_key_condition = None

        # some kludges
        if isinstance(from_date, datetime):
            from_date = from_date.isoformat()
        if isinstance(to_date, datetime):
            to_date = to_date.isoformat()

        if from_date and to_date:
            range_key_condition &= (
                Audit.timestamp.between(from_date, to_date))
        elif from_date:
            range_key_condition &= (Audit.timestamp >= from_date)
        elif to_date:
            range_key_condition &= (Audit.timestamp <= to_date)
        else:
            # describe in docs
            initial_date = datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
            range_key_condition &= (Audit.timestamp >= initial_date.isoformat())

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
                'Timestamp': convert_datetime_to_human_readable(event.timestamp),
                'Parameters': event.parameters,
                'Execution warnings': event.warnings,
                'Result': event.result,
                'Consistency status': 'Compromised' if not valid_event else 'OK'
            }
            if not valid_event:
                invalid_list.append(pretty_value)
            audit_list.append(pretty_value)
        return audit_list, invalid_list
