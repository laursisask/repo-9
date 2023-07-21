import json
from datetime import datetime

from modular_api.models.user_model import User
from modular_api.helpers.constants import ACTIVATED_STATE
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string

_LOG = get_logger('user_service')


class UserService:
    @staticmethod
    def create_user_entity(username, group, password, state=None,
                           creation_date=None):
        _LOG.info(f'Going to create user entity for {username}')
        state = state if state else ACTIVATED_STATE
        creation_date = creation_date if creation_date else datetime.utcnow().\
            replace(microsecond=0)
        groups = [group] if isinstance(group, str) else list(group)
        return User(
            username=username,
            groups=groups,
            password=password,
            state=state,
            creation_date=creation_date
        )

    def save_user_with_recalculated_hash(self, user_item: User):
        hash_sum = self.calculate_user_hash(user_item=user_item)
        user_item.hash = hash_sum
        return User.save(user_item)

    @staticmethod
    def save_user(user_item: User):
        _LOG.info(f'Going to save user entity for {user_item.username}')
        return User.save(user_item)

    @staticmethod
    def scan_users(filter_condition=None):
        _LOG.info('Going to scan all users')
        return User.scan(filter_condition=filter_condition)

    @staticmethod
    def calculate_user_hash(user_item: User):
        _LOG.info('Going calculate hash for User item')
        prepared_user_to_be_hashed = json.dumps(
            user_item.response_object_without_hash()
        )
        user_hash_sum = secure_string(prepared_user_to_be_hashed)
        return user_hash_sum

    @staticmethod
    def describe_user(username):
        _LOG.info(f'Going to describe user by {username} name')
        return User.get_nullable(hash_key=username)

    @staticmethod
    def delete_user(user_item: User):
        _LOG.info(f'Going to delete user by {user_item.username} name')
        user_item.delete()
