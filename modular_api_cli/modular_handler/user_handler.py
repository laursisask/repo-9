import json
import os

import click

from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.request_processor import generate_route_meta_mapping
from modular_api.helpers.utilities import validate_meta_keys
from modular_api.web_service.iam import filter_commands_by_permissions
from modular_api.helpers.constants import (
    BLOCKED_STATE, REMOVED_STATE, ACTIVATED_STATE, ALLOWED_VALUES, AUX_DATA,
    MODULAR_USER_META_TYPES,
)
from modular_api.services.group_service import GroupService
from modular_api.services.permissions_cache_service import \
    permissions_handler_instance, \
    PermissionsService
from modular_api.services.policy_service import PolicyService
from modular_api.helpers.date_utils import convert_datetime_to_human_readable, \
    utc_time_now
from modular_api.helpers.password_util import generate_password, \
    validate_password, \
    secure_string
from modular_api.services.user_service import UserService
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiConfigurationException, \
    ModularApiBadRequestException, ModularApiConflictException, \
    ModularApiUnauthorizedException

SET_META_CMD = ('modular user set_meta_attribute --meta_type allowed_values|'
                'aux_data --key $parameter_name --value $parameter_value')
line_sep = os.linesep
_LOG = get_logger(__name__)


class UserHandler:
    def __init__(self, user_service, group_service, policy_service):
        self.user_service: UserService = user_service
        self.group_service: GroupService = group_service
        self.policy_service: PolicyService = policy_service

    def add_user_handler(self, username, groups, password) -> CommandResponse:
        """
        Adds user to ModularUser table
        :param username: Username that will be set to the user
        :param groups: Group name(s) that will be attached to user
        :param password: User password
        :return: CommandResponse
        """
        _LOG.info(f'Going to add user \'{username}\' to groups {groups}')
        existing_user = self.user_service.describe_user(username=username)
        if existing_user:
            if existing_user.state == BLOCKED_STATE:
                _LOG.error('User already exists but blocked')
                raise ModularApiBadRequestException(
                    f'User \'{username}\' is blocked. To unblock user please '
                    f'execute command:{line_sep}'
                    f'modular user unblock --user {username} --reason '
                    f'<$THE USER UNBLOCKING REASON>')

            elif existing_user.state == REMOVED_STATE:
                _LOG.error('User already exists but marked as removed')
                raise ModularApiBadRequestException(
                    f'User \'{username}\' already exists and marked as '
                    f'\'{REMOVED_STATE}\'')

            elif existing_user.state == ACTIVATED_STATE:
                _LOG.error('User already exists')
                raise ModularApiBadRequestException(
                    f'User \'{username}\' already activated.{line_sep}')
            _LOG.error('User already exists')
            raise ModularApiConflictException(
                f'User \'{username}\' already exists with invalid '
                f'\'{existing_user.state}\' state')

        existing_groups = self.group_service.get_groups_by_name(
            group_names=groups
        )

        if not existing_groups:
            _LOG.error('Can not find all or one from provided groups')
            raise ModularApiBadRequestException(
                f'One or all provided \'{", ".join(groups)}\' group(s) does not '
                f'exist.{line_sep}To add group please execute '
                f'\'modular group add --help\' command first')

        skipped_groups = list()
        for group in groups:
            if group not in [group_name.group_name for group_name in
                             existing_groups]:
                skipped_groups.append(group)

        if skipped_groups:
            _LOG.error('Missing group detected')
            raise ModularApiBadRequestException(
                f'Group(s) you are trying to add to the user is '
                f'missing:{line_sep}{", ".join(skipped_groups)}{line_sep}'
                f'Please remove it`s name(s) from command or add this '
                f'group(s) first'
            )

        invalid_groups = []
        for group in existing_groups:
            if self.group_service.calculate_group_hash(group) != group.hash or \
                    group.state == REMOVED_STATE:
                invalid_groups.append(group.group_name)

        if invalid_groups:
            raise ModularApiBadRequestException(
                f'The following group(s) are invalid:{line_sep}'
                f'{", ".join(invalid_groups)}'
                f'{line_sep}To get more detailed information please execute'
                f'command:{line_sep}modular group describe')

        if password:
            user_password = validate_password(password)
            is_autogenerated = False
        else:
            user_password = generate_password()
            is_autogenerated = True

        user_item = self.user_service.create_user_entity(
            username=username,
            password=secure_string(user_password),
            group=groups
        )

        user_hash_sum = self.user_service.calculate_user_hash(user_item)
        user_item.hash = user_hash_sum
        self.user_service.save_user(user_item=user_item)

        if is_autogenerated:
            autogenerated_message = (f'Autogenerated password: '
                                     f'{user_password}')
            click.echo(autogenerated_message)

        click.echo("PAY ATTENTION: You can get the user password only when "
                   "you add the new user. You cannot retrieve it later. "
                   "If you lose it, you must create a new user or change"
                   "password via 'modular user change_password' command")
        _LOG.info('User successfully activated')
        return CommandResponse(
            message=f'User \'{username}\' has been successfully activated.'
                    f'{line_sep}User added to the following group(s):'
                    f'{line_sep}{", ".join(groups)}')

    def delete_user_handler(self, username) -> CommandResponse:
        """
        Deletes user from ModularUser table
        :param username: Username that will be deleted from white list
        :return: CommandResponse
        """
        _LOG.info(f'Going to delete user \'{username}\'')
        existing_user = self.user_service.describe_user(username=username)
        if not existing_user:
            _LOG.error('User does not exist')
            raise ModularApiConfigurationException(
                f'User \'{username}\' does not exist. Nothing to delete')

        if existing_user.state != ACTIVATED_STATE:
            _LOG.error('User already marked as deleted or blocked')
            raise ModularApiBadRequestException(
                f'User \'{username}\' is blocked or deleted.{line_sep}To get '
                f'more detailed information please execute command:{line_sep}'
                f'modular user describe --username {username}')

        if self.user_service.calculate_user_hash(existing_user) != \
                existing_user.hash:
            click.confirm(
                f'User \'{username}\' is compromised. Command execution '
                f'leads to user entity hash sum recalculation. Are you sure?',
                abort=True)

        existing_user.state = REMOVED_STATE
        existing_user.last_modification_date = utc_time_now().isoformat()
        user_hash_sum = self.user_service.calculate_user_hash(existing_user)
        existing_user.hash = user_hash_sum
        self.user_service.save_user(user_item=existing_user)

        _LOG.info('User successfully deleted')
        return CommandResponse(
            message=f'User {username} has been successfully deleted')

    def block_user_handler(self, username, reason) -> CommandResponse:
        """
        Change user entity state to block
        :param username: Username
        :param reason: The textual reason of user removal
        :return: CommandResponse
        """
        _LOG.info(f'Going to block user \'{username}\' due to {reason}')
        existed_user = self.user_service.describe_user(username=username)
        if not existed_user:
            _LOG.error('User does not exist')
            raise ModularApiConfigurationException(
                f'User \'{username}\' does not exist. Can not block')

        if self.user_service.calculate_user_hash(existed_user) != \
                existed_user.hash:
            click.confirm(
                f'User \'{username}\' is compromised. Command execution leads '
                f'to user entity hash sum recalculation. Are you sure?',
                abort=True)

        existed_user.state = BLOCKED_STATE
        existed_user.state_reason = reason

        existed_user.last_modification_date = utc_time_now().isoformat()
        user_hash_sum = self.user_service.calculate_user_hash(existed_user)
        existed_user.hash = user_hash_sum
        self.user_service.save_user(user_item=existed_user)
        _LOG.info('User successfully blocked')
        return CommandResponse(
            message=f'User \'{username}\' has been successfully blocked')

    def unblock_user_handler(self, username, reason) -> CommandResponse:
        """
        Change user entity state to unblock
        :param username: Username
        :param reason: The textual reason of user returning to whitelist
        :return: CommandResponse
        """
        _LOG.info(f'Going to unblock user \'{username}\' due to {reason}')
        existed_user = self.user_service.describe_user(username=username)
        if not existed_user:
            _LOG.error('User does not exist')
            raise ModularApiConfigurationException(
                f'User \'{username}\' does not exist. Can not unblock')

        if self.user_service.calculate_user_hash(existed_user) != \
                existed_user.hash:
            click.confirm(
                f'User \'{username}\' compromised. Command execution leads '
                f'to user entity hash sum recalculation. Are you sure?',
                abort=True)

        existed_user.state = ACTIVATED_STATE
        existed_user.state_reason = reason

        existed_user.last_modification_date = utc_time_now().isoformat()
        user_hash_sum = self.user_service.calculate_user_hash(existed_user)
        existed_user.hash = user_hash_sum
        self.user_service.save_user(user_item=existed_user)

        _LOG.info('User successfully unblocked')
        return CommandResponse(
            message=f'User \'{username}\' has been successfully unblocked')

    def change_user_password_handler(self, username, password) -> \
            CommandResponse:
        """
        Change user password to administrator defined
        :param username: Username
        :param password: New user password
        :return: CommandResponse
        """
        _LOG.info(f'Going to change password for user \'{username}\'')
        existing_user = self.user_service.describe_user(username=username)
        if not existing_user:
            _LOG.error('User does not exists')
            raise ModularApiConfigurationException(
                f'User \'{username}\' does not exists. Can not change password')

        if existing_user.state != ACTIVATED_STATE:
            _LOG.error('User blocked or deleted')
            raise ModularApiBadRequestException(
                f'User \'{username}\' is blocked or deleted.{line_sep}To get '
                f'more detailed information please execute command:{line_sep}'
                f'modular user describe --username {username}')

        if self.user_service.calculate_user_hash(existing_user) != \
                existing_user.hash:
            click.confirm(
                f'User \'{username}\' is compromised. Command execution leads '
                f'to user entity hash sum recalculation. Are you sure?',
                abort=True)

        existing_user.password = secure_string(
            string_to_secure=validate_password(password=password)
        )

        existing_user.last_modification_date = utc_time_now().isoformat()
        user_hash_sum = self.user_service.calculate_user_hash(existing_user)
        existing_user.hash = user_hash_sum

        self.user_service.save_user(user_item=existing_user)
        _LOG.info('Password successfully updated')
        return CommandResponse(
            message=f'User \'{username}\' password has been updated')

    def change_user_name_handler(self, old_username, new_username) \
            -> CommandResponse:
        _LOG.info(f'Going to change username for user \'{old_username}\'')
        existing_user = self.user_service.describe_user(username=old_username)
        if not existing_user:
            _LOG.error('User does not exists')
            raise ModularApiConfigurationException(
                f'User \'{old_username}\' does not exists. '
                f'Can not change username')

        if existing_user.state != ACTIVATED_STATE:
            _LOG.error('User blocked or deleted')
            raise ModularApiBadRequestException(
                f'User \'{old_username}\' is blocked or deleted.'
                f'{line_sep}To get more detailed information '
                f'please execute command:{line_sep}'
                f'modular user describe --username {old_username}')

        if self.user_service.calculate_user_hash(existing_user) != \
                existing_user.hash:
            click.confirm(
                f'User \'{old_username}\' is compromised. '
                f'Command execution leads to user entity hash '
                f'sum recalculation. Are you sure?',
                abort=True)

        existing_user.last_modification_date = utc_time_now().isoformat()
        existing_user.username = new_username
        self.user_service.save_user_with_recalculated_hash(
            user_item=existing_user
        )
        _LOG.debug(f'New user with username: {new_username} created.')

        _LOG.debug(f'Deleting old user {old_username}')
        existing_user.username = old_username
        self.user_service.delete_user(user_item=existing_user)
        _LOG.info('Username successfully updated')
        return CommandResponse(
            message=f'User \'{old_username}\' name has been '
                    f'updated to {new_username}')

    def manage_user_groups_handler(self, username, groups, action) -> \
            CommandResponse:
        """
        Add or remove user to the group(s)
        :param username: Username
        :param groups: Group name(s) that will be attached or detached to user
        :param action: attach or detach group
        :return: CommandResponse
        """
        _LOG.info(f'Going to {action} user \'{username}\' in group(s)')
        groups = list(set(groups))
        existing_user = self.user_service.describe_user(username=username)
        if not existing_user:
            _LOG.error('User does not exists')
            raise ModularApiConfigurationException(
                f'User \'{username}\' does not exist. Please check spelling')

        if existing_user.state != ACTIVATED_STATE:
            _LOG.error('User blocked or deleted')
            raise ModularApiBadRequestException(
                f'User {username} is blocked or deleted{line_sep}To get more '
                f'detailed information please execute command:{line_sep}'
                f'modular user describe --username {username}')

        if self.user_service.calculate_user_hash(existing_user) != \
                existing_user.hash:
            click.confirm(
                f'User \'{username}\' is compromised. Command execution leads '
                f'to user entity hash sum recalculation. Are you sure?',
                abort=True)

        requested_group_items = self.group_service.get_groups_by_name(
            group_names=groups)
        if not requested_group_items:
            raise ModularApiBadRequestException(
                f'One or all from requested group(s) does not exist. '
                f'Group(s):{line_sep}{groups}')

        if len(groups) != len(requested_group_items):
            retrieved_group_names = [group.group_name
                                     for group in requested_group_items]
            not_existed_policies = [group for group in groups
                                    if group not in retrieved_group_names]
            if not_existed_policies:
                raise ModularApiBadRequestException(
                    f'The following groups does not exists: '
                    f'{", ".join(not_existed_policies)}')

        invalid_groups = []
        for group in requested_group_items:
            if self.group_service.calculate_group_hash(group) != group.hash \
                    and group.state != ACTIVATED_STATE:
                invalid_groups.append(group.group_name)

        if invalid_groups:
            raise ModularApiBadRequestException(
                f'The following group(s) compromised or deleted:{line_sep}'
                f'{", ".join(invalid_groups)}.{line_sep}To get more detailed'
                f' information please execute command:{line_sep}'
                f'modular group describe')

        warnings_list = []
        user_groups = existing_user.groups
        if action == 'add':
            existed_group_in_user = set(groups).intersection(user_groups)
            if existed_group_in_user:
                warnings_list.append(
                    f'User already attached to the following groups: '
                    f'{", ".join(existed_group_in_user)}')
            existing_user.groups = list(set(user_groups).union(set(groups)))

        elif action == 'remove':
            not_existed_group_in_user = set(groups).difference(user_groups)
            if not_existed_group_in_user:
                warnings_list.append(
                    f'The following groups does not attached to the user: '
                    f'{", ".join(not_existed_group_in_user)}')
            existing_user.groups = list(set(user_groups) - set(groups))
        else:
            raise ModularApiBadRequestException('Invalid action requested')

        existing_user.last_modification_date = utc_time_now().isoformat()
        user_hash_sum = self.user_service.calculate_user_hash(existing_user)
        existing_user.hash = user_hash_sum
        self.user_service.save_user(user_item=existing_user)
        _LOG.info('User entity updated')
        if warnings_list:
            _LOG.warning(f'Command executed with following warning(s): '
                         f'{warnings_list}')
        return CommandResponse(
            message=f'User \'{username}\' has been updated',
            warnings=warnings_list)

    @staticmethod
    def check_user_items_exist(user_items: list) -> None:
        if not user_items:
            raise ModularApiBadRequestException(
                'User(s) does not exist. To add user please execute '
                '\'modular user add\' command')

    def resolve_policy_allowed_actions(self, policies):
        actions = []
        errors = []
        for policy in policies:
            received_policy = self.policy_service.describe_policy(
                policy_name=policy)
            if not received_policy:
                errors.append(f'Policy \'{policy}\' does not exist')
                continue
            if received_policy.hash != self.policy_service.calculate_policy_hash(
                    policy_item=received_policy):
                errors.append(
                    f'Policy \'{policy}\' is compromised. Calculated hash sum is '
                    f'different from existed in entity.')
            actions.extend(received_policy.content)
        return actions, errors

    def validate_groups_policies_and_resolve_actions(self, groups):
        errors_list = []
        actions_list = []
        for group in groups:
            received_group = self.group_service.describe_group(
                group_name=group)
            if not received_group:
                errors_list.append(f'Group \'{group}\' does not exist')
                continue

            if received_group.hash != self.group_service.calculate_group_hash(
                    group_item=received_group):
                errors_list.append(
                    f'Group {group} is compromised. Calculated hash sum is '
                    f'different from existed in entity.')

            actions, errors = self.resolve_policy_allowed_actions(
                policies=received_group.policies
            )
            errors_list.extend(errors)
            actions_list.extend(actions)
        return errors_list, actions_list

    @staticmethod
    def prettify_user_item(user, user_compromised,
                           policy_group_compromised=False):
        is_compromised = any([user_compromised, policy_group_compromised])
        return {
            'Username': user.username,
            'Groups': user.groups,
            'State': user.state,
            'State reason': user.state_reason,
            'User meta': user.meta.as_dict() if user.meta else None,
            'Modification date': convert_datetime_to_human_readable(
                datetime_object=user.last_modification_date
            ),
            'Creation Date': convert_datetime_to_human_readable(
                datetime_object=user.creation_date
            ),
            'Consistency status': 'Compromised' if is_compromised else 'OK'
        }

    def describe_single_user(self, username, json_response):
        existed_user = self.user_service.describe_user(
            username=username)

        if not existed_user:
            raise ModularApiBadRequestException(
                f'No such user: \'{username}\'')

        policies_groups_warnings, _ = \
            self.validate_groups_policies_and_resolve_actions(
                groups=existed_user.groups
            )

        user_compromised = self.user_service.calculate_user_hash(
            user_item=existed_user) != existed_user.hash

        is_policies_groups_compromised = True if policies_groups_warnings else False
        pretty_user = self.prettify_user_item(
            user=existed_user,
            user_compromised=user_compromised,
            policy_group_compromised=is_policies_groups_compromised
        )

        if json_response:
            return CommandResponse(
                message=json.dumps(pretty_user, indent=4)
            )

        return CommandResponse(
            table_title='User description',
            warnings=policies_groups_warnings,
            items=[pretty_user])

    def policy_simulator_handler(self, user_name, user_group, policy_name,
                                 requested_command):
        warnings_list = []
        policies = []
        item_name = ''
        item = ''
        if user_name:
            existed_user = self.user_service.describe_user(
                username=user_name)

            if not existed_user:
                raise ModularApiBadRequestException(
                    f'No such user: \'{user_name}\'')

            warnings_list, policies = \
                self.validate_groups_policies_and_resolve_actions(
                    groups=existed_user.groups
                )
            item, item_name = 'user', user_name

        elif user_group:
            warnings_list, policies = \
                self.validate_groups_policies_and_resolve_actions(
                    groups=[user_group]
                )
            item, item_name = 'group', user_group
        elif policy_name:
            policies, warnings_list = self.resolve_policy_allowed_actions(
                policies=[policy_name]
            )
            item, item_name = 'policy', policy_name

        if warnings_list:
            return CommandResponse(
                message='Any action can not be performed due to '
                        'user/group/policy invalid configuration',
                warnings=warnings_list
            )

        if not requested_command.startswith('admin '):
            raise ModularApiBadRequestException(
                'Incorrect spelling. All commands should starting '
                'with "admin ..."'
            )
        if '-' in requested_command:
            raise ModularApiBadRequestException(
                'Incorrect spelling. "-" and "--" symbols are not allowed. '
                'Check spelling'
            )
        available_commands = permissions_handler_instance().available_commands
        filtered_commands = filter_commands_by_permissions(available_commands,
                                                           policies)

        route_mapping = generate_route_meta_mapping(
            commands_meta=filtered_commands)

        init_cmd = requested_command
        requested_command = requested_command.split()
        path = '/'.join(requested_command).replace('admin', '')
        # for admin root commands
        # if will be added new one -> add to list:
        if path == '/get_operation_status':
            path = '/admin/get_operation_status'
        # ----------------------------------------
        effect = 'ALLOW' if path in route_mapping.keys() else 'DENY'

        return CommandResponse(
            f'Checked for {item}: {item_name}{os.linesep}'
            f'Command: {init_cmd}{os.linesep}'
            f'Status: {effect}{os.linesep}'
        )

    def describe_user_handler(self, username, table_response,
                              json_response) -> CommandResponse:
        """
        Describes user entity from User model or list all existed users
        :param username: Username that will be deleted from white list
        :param table_response: output will be in table format
        :param json_response: output will be in json format
        :return: CommandResponse
        """

        if table_response and json_response:  # todo why is it here
            _LOG.error('Wrong parameters passed')
            raise ModularApiBadRequestException(
                'Please specify only one parameter - table or json')

        _LOG.info(f'Going to describe user \'{username}\'')
        if username:
            return self.describe_single_user(username=username,
                                             json_response=json_response)

        existed_users = self.user_service.scan_users()
        self.check_user_items_exist(user_items=existed_users)

        pretty_users = []
        invalid = 0
        for user in existed_users:
            is_compromised = self.user_service.calculate_user_hash(
                user_item=user) != user.hash
            if is_compromised:
                invalid += 1

            pretty_user_item = self.prettify_user_item(
                user=user,
                user_compromised=is_compromised
            )
            pretty_users.append(pretty_user_item)
        valid_title = 'User(s) description'
        compromised_title = f'User(s) description{os.linesep}WARNING! ' \
                            f'{invalid} compromised users have been detected.'

        if json_response:
            return CommandResponse(
                message=json.dumps(pretty_users, indent=4)
            )

        return CommandResponse(
            table_title=compromised_title if invalid else valid_title,
            items=pretty_users)

    def set_user_meta_handler(
            self,
            username: str,
            meta_type: str,
            key: str,
            values: tuple,
    ) -> CommandResponse:
        _LOG.info(
            f"Going to set meta with type '{meta_type}' for the user '{username}'"
        )
        user = self.check_existence_and_get_user(username)
        self.check_user_validness(user)
        user.meta = user.meta or {}
        if meta_type not in user.meta:
            user.meta[meta_type] = {}
        match meta_type:
            case "allowed_values":
                validate_meta_keys(key)
                action = 'replaced' if key in user.meta[meta_type] else 'set'
                user.meta[meta_type][key] = list(values)
            case "aux_data":
                action = 'replaced' if key in user.meta[meta_type] else 'set'
                user.meta[meta_type][key] = list(values)
            case _:
                raise ModularApiBadRequestException(
                    f"Invalid meta_type. Should be either {ALLOWED_VALUES} or "
                    f"{AUX_DATA}"
                )
        user.last_modification_date = utc_time_now().isoformat()
        self.user_service.save_user_with_recalculated_hash(user)
        log_and_return_message = (
            f"The '{meta_type}' in the 'meta' data for the user '{username}' "
            f"has been '{action}' successfully."
        )
        _LOG.info(log_and_return_message)
        return CommandResponse(message=log_and_return_message)

    def update_user_meta_handler(
            self,
            username: str,
            meta_type: str,
            key: str,
            values: tuple,
    ) -> CommandResponse:
        _LOG.info(f'Going to update user \'{username}\' meta')
        user = self.check_existence_and_get_user(username)
        self.check_user_validness(user)
        if not user.meta or not user.meta.as_dict().get(meta_type):
            _LOG.error('There is no meta to update')
            raise ModularApiBadRequestException(
                f"User '{username}' has no meta or it is empty, nothing to "
                f"update.{os.linesep}Please set meta first with the command "
                f"'{SET_META_CMD}'"
            )
        if key not in user.meta.as_dict().get(meta_type).keys():
            _LOG.error(f'Invalid key \'{key}\' for meta updating')
            raise ModularApiBadRequestException(
                f"User '{username}' has no parameter name '{key}' in meta."
                f"{meta_type}' or it is empty, nothing to update.{os.linesep}"
                f"Please set meta first with the command {SET_META_CMD}'"
            )
        match meta_type:
            case "allowed_values":
                validate_meta_keys(key)
                values_list = user.meta[meta_type].get(key)
                user.meta[meta_type][key] = list(set(values_list) | set(values))
            case "aux_data":
                values_list = user.meta[meta_type].get(key)
                user.meta[meta_type][key] = list(set(values_list) | set(values))
            case _:
                raise ModularApiBadRequestException(
                    f"Invalid meta_type. Should be either {ALLOWED_VALUES} or "
                    f"{AUX_DATA}"
                )
        user.last_modification_date = utc_time_now().isoformat()
        self.user_service.save_user_with_recalculated_hash(user)
        _LOG.error('User meta successfully updated')
        return CommandResponse(
            message=f'Meta information for user \'{username}\' has been '
                    f'successfully updated'
        )

    def delete_user_meta_handler(
            self,
            username: str,
            keys: tuple,
            meta_type: str,
    ) -> CommandResponse:
        _LOG.info(f'Going to delete meta from the user \'{username}\'')
        user = self.check_existence_and_get_user(username)
        self.check_user_validness(user)
        if not user.meta or not user.meta.as_dict().get(meta_type):
            _LOG.error('There is no meta to delete')
            raise ModularApiBadRequestException(
                f"User '{username}' has no meta or it is empty, nothing to "
                f"delete.{os.linesep}Please set meta first with the command "
                f"'{SET_META_CMD}'"
            )
        skipped_keys = []
        removed_keys = []
        for key in keys:
            if key not in user.meta[meta_type]:
                skipped_keys.append(key)
                continue
            user.meta[meta_type].pop(key)
            removed_keys.append(key)
        if removed_keys:
            user.last_modification_date = utc_time_now().isoformat()
            self.user_service.save_user_with_recalculated_hash(user)
            message = f'Deleted parameter(s) name from \'{username}\' meta: ' \
                      f'{removed_keys}'
        else:
            message = f'No parameter(s) name has been removed from ' \
                      f'\'{username}\' meta'
        if skipped_keys:
            message += f'{os.linesep}Next parameter(s) name deletion skipped ' \
                       f'due to its absence in user meta: {skipped_keys}'
        _LOG.info(f'Keys {keys} successfully deleted from user meta')
        return CommandResponse(message=message)

    def reset_user_meta_handler(self, username):
        _LOG.info(f'Going to delete meta from the user \'{username}\'')
        user = self.check_existence_and_get_user(username)
        self.check_user_validness(user)
        if not user.meta or not user.meta.as_dict():
            _LOG.error('User has no meta, nothing to delete')
            raise ModularApiBadRequestException(
                f'User \'{username}\' has no meta, nothing to reset.'
                f'{os.linesep}Please set meta first with the command '
                f'\'{SET_META_CMD}\''
            )
        user.meta = {}
        user.last_modification_date = utc_time_now().isoformat()
        self.user_service.save_user_with_recalculated_hash(user)
        _LOG.info('All user meta successfully deleted')
        return CommandResponse(
            message=f'All data in user \'{username}\' meta has been deleted'
        )

    def describe_user_meta_handler(
            self,
            username: str,
            json_response: bool,
            table_response: bool,
    ) -> CommandResponse:
        if table_response and json_response:
            _LOG.error('Wrong parameters passed')
            raise ModularApiBadRequestException(
                'Please specify only one parameter - table or json'
            )
        _LOG.info(f'Going to describe \'{username}\' user meta')
        user = self.check_existence_and_get_user(username)
        items = []
        meta_values = user.meta.as_dict() if user.meta else {}
        if not meta_values or not (
                meta_values.get(ALLOWED_VALUES) or meta_values.get(AUX_DATA)
        ):
            return CommandResponse(
                message=f'There is nothing to describe. The user \'{username}\''
                        f' has no `meta` or it is empty.'
            )
        for section in MODULAR_USER_META_TYPES:
            section_data = user.meta.as_dict().get(section)
            if section_data is None:
                continue
            for item, values in section_data.items():
                values.sort()
                result = ', '.join(values)
                items.append(
                    {
                        "Type of meta": section,
                        "Parameter name": item,
                        "Parameter values": result,
                    }
                )
        _LOG.info('User meta successfully described')
        if json_response:
            return CommandResponse(
                message=json.dumps(items, indent=4)
            )
        return CommandResponse(
            table_title=f"Meta information for user \'{username}\'",
            items=items
        )

    def check_user_validness(self, user):
        try:
            PermissionsService(
                user_service=self.user_service,
                group_service=self.group_service,
                policy_service=self.policy_service
            ).check_user_item_is_valid(user)
        except ModularApiUnauthorizedException:
            raise ModularApiBadRequestException(
                'The User item you are trying to modify is compromised. '
                'Can not perform command execution'
            )

    def check_existence_and_get_user(self, username):
        user = self.user_service.describe_user(username=username)
        if not user:
            raise ModularApiBadRequestException(
                f'User with name \'{username}\' does not exist'
            )
        return user
