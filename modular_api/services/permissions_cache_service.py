import json
import os
from pathlib import Path

from modular_api.models.user_model import User
from modular_api.helpers.constants import ACTIVATED_STATE, ALLOWED_VALUES
from modular_api.helpers.exceptions import (
    ModularApiUnauthorizedException, ModularApiBadRequestException,
)
from modular_api.helpers.jwt_auth import decode_jwt_token
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string
from modular_api.services import SERVICE_PROVIDER
from modular_api.services.group_service import GroupService
from modular_api.services.policy_service import PolicyService
from modular_api.services.user_service import UserService
from modular_api.web_service import WEB_SERVICE_PATH, COMMANDS_BASE_FILE_NAME
from modular_api.web_service.iam import filter_commands_by_permissions

_LOG = get_logger(__name__)


class PermissionsService:
    def __init__(self, user_service, group_service, policy_service):
        self.available_commands = self.get_available_commands()
        self.group_allowed_commands_mapping = {}

        self.user_service: UserService = user_service
        self.group_service: GroupService = group_service
        self.policy_service: PolicyService = policy_service

    @staticmethod
    def get_available_commands() -> dict:
        commands_base_path = Path(__file__).parent.parent / WEB_SERVICE_PATH / COMMANDS_BASE_FILE_NAME
        _LOG.info(f'Getting available commands from {commands_base_path}')
        if not os.path.isfile(commands_base_path):
            return {}
            # unable__to_run_server_message = 'Can not run server without any ' \
            #                                 'installed modules'
            # _LOG.error(unable__to_run_server_message)
            # raise ModularApiConfigurationException(unable__to_run_server_message)

        with open(commands_base_path) as file:
            available_commands = json.load(file)
        return available_commands

    def resolve_available_commands(self, group_names, empty_cache):
        _LOG.info(f'Available commands resolving for \'{group_names}\' '
                  f'groups')
        policy_aggregation = []
        for group in group_names:

            if empty_cache or group not in self.group_allowed_commands_mapping:
                policy_aggregation.extend(
                    self.generate_allowed_commands(group_name=group))
            else:
                policy_aggregation.extend(
                    self.group_allowed_commands_mapping[group])

        user_allowed_commands = filter_commands_by_permissions(
            available_commands=self.available_commands,
            group_policy=policy_aggregation)
        return user_allowed_commands

    def generate_allowed_commands(self, group_name):
        _LOG.info(f'Available commands generating for {group_name} '
                  f'groups')

        group_item = self.group_service.describe_group(group_name=group_name)

        is_hash_invalid = self.group_service.calculate_group_hash(group_item) \
            != group_item.hash
        is_group_disabled = group_item.state != ACTIVATED_STATE

        if is_hash_invalid or is_group_disabled:
            if is_hash_invalid:
                possible_reason = 'compromised item'
            elif is_group_disabled:
                possible_reason = 'inactive state'
            else:
                possible_reason = 'compromised item and inactive state'
            _LOG.error(f'{group_item.group_name} group invalid. Possible '
                       f'reason: {possible_reason}')

            raise ModularApiUnauthorizedException(
                'Provided credentials are invalid or the access was revoked, '
                'please contact service administrator')

        group_policy = []
        for policy in group_item.policies:
            policy_item = self.policy_service.describe_policy(
                policy_name=policy)

            is_policy_hash_invalid = self.policy_service.calculate_policy_hash(
                policy_item=policy_item) != policy_item.hash
            is_policy_deactivated = policy_item.state != ACTIVATED_STATE

            if is_policy_hash_invalid or is_policy_deactivated:
                if is_policy_hash_invalid:
                    possible_reason = 'compromised item'
                elif is_policy_deactivated:
                    possible_reason = 'inactive state'
                else:
                    possible_reason = 'compromised item and inactive state'
                _LOG.error(f'{group_item.group_name} policy invalid. Possible '
                           f'reason: {possible_reason}')
                raise ModularApiUnauthorizedException(
                    'Provided credentials are invalid or the access was '
                    'revoked, please contact service administrator')

            for policy_content in policy_item.content:
                group_policy.append(policy_content)

        self.group_allowed_commands_mapping[group_item.group_name] = \
            group_policy

        return self.group_allowed_commands_mapping[group_item.group_name]

    def get_user_item_or_raise_error(self, username: str) -> User:
        if not username:
            _LOG.info('Username is empty')
            raise ModularApiBadRequestException('Username is empty')
        _LOG.info(f'Going to get user item by {username} username')
        user_item = self.user_service.describe_user(username=username)
        if not user_item:
            _LOG.info(f'[auth] User does not exist: {username}')
            raise ModularApiUnauthorizedException('User does not exist')
        return user_item

    def check_user_item_is_valid(self, user_item):
        _LOG.info(f'Going to check if {user_item.username} user able to '
                  f'perform commands')
        calculated_hash = self.user_service.calculate_user_hash(
            user_item=user_item
        )
        if calculated_hash != user_item.hash:
            _LOG.error(f'{user_item.username} user item compromised')
            raise ModularApiUnauthorizedException(
                'Provided credentials are invalid or the access was '
                'revoked, please contact service administrator')
        elif user_item.state != ACTIVATED_STATE:
            _LOG.error(f'{user_item.username} user item in inactive state')
            raise ModularApiUnauthorizedException(
                'Provided credentials are invalid or the access was '
                'revoked, please contact service administrator')

    def authenticate_user(
            self,
            username: str,
            password: str | None = None,
            token: str | None = None,
            empty_cache: bool | None = None,
    ) -> tuple:
        if not any([password, token]):
            raise ModularApiUnauthorizedException(
                'Password or token was not provided'
            )
        if token:
            username = self.validate_jwt_and_get_user(token=token)
            if not username:
                _LOG.info(
                    f'[auth] Invalid JWT: {username}. Access denied')
                raise ModularApiUnauthorizedException('Access denied')
            user_item = self.get_user_item_or_raise_error(username=username)
            self.check_user_item_is_valid(user_item=user_item)
        else:
            user_item = self.get_user_item_or_raise_error(username=username)
            self.check_user_item_is_valid(user_item=user_item)
            is_password_valid = self.validate_password(
                username=username,
                user_password=user_item.password,
                provided_password=password,
            )
            if not is_password_valid:
                _LOG.info(
                    f'[auth] Invalid password: {username}. Access denied'
                )
                raise ModularApiUnauthorizedException('Access denied')

        available_commands = self.resolve_available_commands(
            group_names=user_item.groups,
            empty_cache=empty_cache
        )
        user_meta = (
            user_item.meta.as_dict().get(ALLOWED_VALUES, {})
        ) if user_item.meta else {}
        return available_commands, user_meta

    @staticmethod
    def validate_jwt_and_get_user(token: str) -> str | None:
        payload = decode_jwt_token(token)
        if not payload:
            _LOG.info('[auth] User is NOT authenticated with JWT')
            return
        username = payload.get('username')
        _LOG.info(f'[auth] User {username} is authenticated with JWT')
        return username

    @staticmethod
    def validate_password(username, user_password, provided_password):
        if secure_string(provided_password) == user_password:
            _LOG.info(f'[auth] User {username} is authenticated by password')
            return True
        _LOG.info(f'[auth] User {username} is NOT authenticated by password')
        return False


def permissions_handler_instance():
    return PermissionsService(
        user_service=SERVICE_PROVIDER.user_service,
        group_service=SERVICE_PROVIDER.group_service,
        policy_service=SERVICE_PROVIDER.policy_service
    )
