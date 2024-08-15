import json
from typing import Iterable

from pynamodb.pagination import ResultIterator

from modular_api.helpers.constants import ACTIVATED_STATE
from modular_api.helpers.date_utils import utc_time_now
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string
from modular_api.models.group_model import Group

_LOG = get_logger(__name__)


class GroupService:
    @staticmethod
    def create_group_entity(group_name: str, policies: list[str],
                            state: str = ACTIVATED_STATE):
        _LOG.info(f'Creating \'{group_name}\' group')
        return Group(
            group_name=group_name,
            policies=policies,
            state=state,
            creation_date=utc_time_now().isoformat()
        )

    @staticmethod
    def save_group(group_item: Group) -> None:
        _LOG.info(f'Saving \'{group_item}\' group')
        group_item.save()

    @staticmethod
    def scan_groups(filter_condition=None) -> ResultIterator[Group]:
        _LOG.info('Scanning groups')
        return Group.scan(filter_condition=filter_condition)

    @staticmethod
    def get_groups_by_name(group_names: Iterable[str]) -> list[Group]:
        _LOG.info(f'Groups batch getting by provided names: '
                  f'{group_names}')
        return list(Group.batch_get(items=group_names))

    @staticmethod
    def describe_group(group_name) -> Group | None:
        _LOG.info(f'Describing group \'{group_name}\'')
        return Group.get_nullable(hash_key=group_name)

    @staticmethod
    def calculate_group_hash(group_item: Group) -> str:
        _LOG.info(f'Calculating \'{group_item.group_name}\' group hash')
        prepared_group_to_be_hashed = json.dumps(
            group_item.response_object_without_hash(),
            sort_keys=True
        )
        return secure_string(prepared_group_to_be_hashed)

    @staticmethod
    def delete_group(group_item: Group) -> None:
        _LOG.info(f'Deleting group \'{group_item.group_name}\'')
        group_item.delete()
