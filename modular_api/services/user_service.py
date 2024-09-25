import json

from pynamodb.pagination import ResultIterator

from modular_api.helpers.constants import ACTIVATED_STATE
from modular_api.helpers.date_utils import utc_time_now
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string
from modular_api.models.user_model import User

_LOG = get_logger(__name__)


class UserService:
    @staticmethod
    def create_user_entity(username: str, group: str | list[str],
                           password: str, state: str = ACTIVATED_STATE
                           ) -> User:
        _LOG.info(f'User \'{username}\' entity creation')
        if isinstance(group, str):
            group = [group]
        return User(
            username=username,
            groups=group,
            password=password,
            state=state,
            creation_date=utc_time_now().isoformat()
        )

    def save_user_with_recalculated_hash(self, user_item: User) -> None:
        _LOG.info(f'Saving recalculated hash for the user \'{user_item.username}\'')
        user_item.hash = self.calculate_user_hash(user_item=user_item)
        user_item.save()

    @staticmethod
    def save_user(user_item: User) -> None:
        _LOG.info(f'Saving user \'{user_item.username}\'')
        user_item.save()

    @staticmethod
    def scan_users(filter_condition=None) -> ResultIterator[User]:
        _LOG.info('Going to scan all users')
        return User.scan(filter_condition=filter_condition)

    @staticmethod
    def calculate_user_hash(user_item: User) -> str:
        _LOG.info(f'Calculating hash for \'{user_item.username}\'')
        prepared_user_to_be_hashed = json.dumps(
            user_item.response_object_without_hash(),
            sort_keys=True
        )
        return secure_string(prepared_user_to_be_hashed)

    @staticmethod
    def describe_user(username: str) -> User | None:
        _LOG.info(f'Describing user \'{username}\'')
        return User.get_nullable(hash_key=username)

    @staticmethod
    def delete_user(user_item: User) -> None:
        _LOG.info(f'Deleting user \'{user_item.username}\'')
        user_item.delete()
