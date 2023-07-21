import json
from datetime import datetime

from modular_api.helpers.constants import ACTIVATED_STATE
from modular_api.models.group_model import Group
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string

_LOG = get_logger('group_service')


class GroupService:
    @staticmethod
    def create_group_entity(group_name, policies, state=None,
                            creation_date=None):
        _LOG.info(f'Going to create group entity for {group_name} group')
        state = state if state else ACTIVATED_STATE
        creation_date = creation_date if creation_date else datetime.utcnow(). \
            replace(microsecond=0)
        return Group(
            group_name=group_name,
            policies=policies,
            state=state,
            creation_date=creation_date
        )

    @staticmethod
    def save_group(group_item):
        _LOG.info(f'Going to save {group_item} group')
        return Group.save(group_item)

    @staticmethod
    def scan_groups(filter_condition=None):
        _LOG.info('Going to scan groups')
        return Group.scan(filter_condition=filter_condition)

    @staticmethod
    def get_groups_by_name(group_names):
        _LOG.info(f'Going to batch get groups by provided names: '
                  f'{group_names}')
        return list(Group.batch_get(items=group_names))


    @staticmethod
    def describe_group(group_name):
        _LOG.info(f'Going to describe group by provided {group_name} name')
        return Group.get_nullable(hash_key=group_name)

    @staticmethod
    def calculate_group_hash(group_item: Group):
        _LOG.info(f'Going to calculate group hash by provided '
                  f'{group_item.group_name} name')
        prepared_group_to_be_hashed = json.dumps(
            group_item.response_object_without_hash()
        )
        user_hash_sum = secure_string(prepared_group_to_be_hashed)
        return user_hash_sum

    @staticmethod
    def get_groups_by_name(group_names):
        _LOG.info(f'Going to batch get groups by provided names: '
                  f'{group_names}')
        return list(Group.batch_get(items=group_names))

    @staticmethod
    def delete_group(group_item: Group):
        _LOG.info(f'Going to delete group by provided name: '
                  f'{group_item.group_name}')
        group_item.delete()
