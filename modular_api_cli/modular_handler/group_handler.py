import json
import os

import click

from modular_api.helpers.log_helper import get_logger
from modular_api.models.user_model import User
from modular_api.helpers.constants import REMOVED_STATE, ACTIVATED_STATE
from modular_api.services.group_service import GroupService
from modular_api.services.policy_service import PolicyService
from modular_api.services.user_service import UserService
from modular_api.helpers.date_utils import convert_datetime_to_human_readable, utc_time_now
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiBadRequestException, \
    ModularApiConflictException

line_sep = os.linesep
_LOG = get_logger(__name__)


class GroupHandler:
    def __init__(self, group_service, policy_service, user_service):
        self.user_service: UserService = user_service
        self.group_service: GroupService = group_service
        self.policy_service: PolicyService = policy_service

    def add_group_handler(self, group: str, policies: list) -> CommandResponse:
        """
        Add group to ModularGroup table
        :param group: group name
        :param policies: Policies list which will be attached to group
        :return: CommandResponse
        """
        _LOG.info(f'Going to add group \'{group}\' with policies \'{policies}\'')
        policies = list(set(policies))

        existed_group = self.group_service.describe_group(group_name=group)
        if existed_group:
            if existed_group.state == REMOVED_STATE:
                _LOG.error('Specified group already exists')
                raise ModularApiBadRequestException(
                    f'Group with name {group} already exists and marked as '
                    f'\'{REMOVED_STATE}\'')

            elif existed_group.state == ACTIVATED_STATE:
                _LOG.error('Specified group already exists')
                raise ModularApiBadRequestException(
                    f'Group with name \'{group}\' already exists. Please '
                    f'change name to another one or configure existing '
                    f'\'{group}\' group with new policies by command:'
                    f'{line_sep}modular group add_policy --group {group} '
                    f'--policy $policy_name{line_sep}In case if you need add '
                    f'several policies at one time use the next syntax:'
                    f'{line_sep}modular group add_policy --group {group} '
                    f'--policy $policy_name_1 --policy $policy_name_2 '
                    f'--policy $policy_name_N')

            _LOG.error('Specified group already exists')
            raise ModularApiConflictException(
                f'Group with name \'{group}\' already exists with invalid '
                f'\'{existed_group.state}\' state')

        existing_policies = self.policy_service.get_policies_by_name(
            policy_names=policies
        )

        if not existing_policies:
            _LOG.error('Specified policies does not exist')
            raise ModularApiBadRequestException(
                f'Policy(ies) you are trying to add to the group \'{group}\' '
                f'does not exist. Please add policy(ies) first via command:'
                f'{line_sep}modular policy add'
            )

        skipped_policies = list()
        for policy_name in policies:
            if policy_name not in [policy.policy_name for policy in existing_policies]:
                skipped_policies.append(policy_name)
        if skipped_policies:
            _LOG.error('Specified policies does not exist')
            raise ModularApiBadRequestException(
                f'Policy(ies) you are trying to add to the group is '
                f'missing:{line_sep}{", ".join(skipped_policies)}{line_sep}'
                f'Please remove it`s name(s) from command or add this '
                f'policy(ies) first'
            )

        invalid_policies = []
        for policy in existing_policies:
            if self.policy_service.calculate_policy_hash(policy) != policy.hash \
                    or policy.state != ACTIVATED_STATE:
                invalid_policies.append(policy.policy_name)

        if invalid_policies:
            _LOG.error('Provided policies compromised or deleted')
            raise ModularApiBadRequestException(
                f'Provided policies compromised or deleted: '
                f'{", ".join(invalid_policies)}.{line_sep}To get more detailed '
                f'information please execute command:{line_sep}'
                f'modular policy describe')

        group_item = self.group_service.create_group_entity(
            group_name=group,
            policies=policies
        )

        group_hash_sum = self.group_service.calculate_group_hash(
            group_item=group_item
        )
        group_item.hash = group_hash_sum

        self.group_service.save_group(group_item=group_item)

        _LOG.info(f'Group with name \'{group}\' successfully added')
        return CommandResponse(
            message=f'Group with name \'{group}\' successfully added. Attached '
                    f'policy(ies): {policies}')

    def manage_group_policies_handler(self, group: str, policies: list,
                                      action: str) -> CommandResponse:
        """
        Adds policies to existed group entity
        :param group: group name which will be updated
        :param policies: Policies list which will be attached/detached to/from group
        :param action: add or remove action
        :return: CommandResponse
        """

        policies = list(set(policies))

        group_item = self.group_service.describe_group(group_name=group)
        if not group_item:
            _LOG.error(f'Group with name \'{group}\' does not exist')
            raise ModularApiBadRequestException(
                f'Group with name \'{group}\' does not exist. Please check '
                f'group name spelling or add group via command:{line_sep}'
                f'modular group add --group {group} --policy $policy_name_1 '
                f'--policy $policy_name_2 --policy $policy_name_N')

        if group_item.state != ACTIVATED_STATE:
            _LOG.error(f'Group with name \'{group}\' is blocked or deleted')
            raise ModularApiBadRequestException(
                f'Group with name \'{group}\' is blocked or deleted. To get '
                f'more detailed information please execute command:{line_sep}'
                f'modular group describe --group {group}')

        if self.group_service.calculate_group_hash(group_item) != \
                group_item.hash:
            click.confirm(
                f'Group with name \'{group}\' is compromised. Command '
                f'execution leads to group entity hash sum recalculation. '
                f'Are you sure?', abort=True)

        retrieved_policies = self.policy_service.get_policies_by_name(
            policy_names=policies
        )
        if not retrieved_policies:
            not_existed_policy = set(policies).intersection(group_item.policies)
            if not_existed_policy and action == 'remove':
                click.confirm(
                    'Provided policy attached to group, but policy entity '
                    'does not exists. Possible reason is ModularPolicy '
                    f'collection compromised and the following policy entities'
                    f' dropped from DB: {not_existed_policy}. Are you about '
                    f'group hash recalculation?',
                    abort=True
                )
                for policy in not_existed_policy:
                    group_item.policies.remove(policy)
                group_hash_sum = self.group_service.calculate_group_hash(
                    group_item)
                group_item.hash = group_hash_sum
                self.group_service.save_group(group_item=group_item)
                return CommandResponse(
                    message='Group item hash successfully recalculated. '
                            'Please execute command again'
                )
            raise ModularApiBadRequestException(
                f'Not existed policy(ies) requested: {policies}')
        if len(policies) != len(retrieved_policies):
            retrieved_policy_names = [policy.policy_name
                                      for policy in retrieved_policies]
            not_existed_policies = [policy for policy in policies
                                    if policy not in retrieved_policy_names]
            not_existed_policy = set(not_existed_policies).intersection(
                group_item.policies)
            if not_existed_policy and action == 'remove':
                click.confirm(
                    'Provided policy attached to group, but policy entity '
                    'does not exists. Possible reason is ModularPolicy '
                    f'collection compromised and the following policy entities'
                    f' dropped from DB: {not_existed_policy}. Are you about '
                    f'group hash recalculation?',
                    abort=True
                )
                for policy in not_existed_policy:
                    group_item.policies.remove(policy)
                group_hash_sum = self.group_service.calculate_group_hash(
                    group_item)
                group_item.hash = group_hash_sum
                self.group_service.save_group(group_item=group_item)
                return CommandResponse(
                    message='Group item hash successfully recalculated. '
                            'Please execute command again'
                )

            if not_existed_policies:
                raise ModularApiBadRequestException(
                    f'Provided policies does not exist: '
                    f'{", ".join(not_existed_policies)}')

        invalid_policies = []
        for policy in retrieved_policies:
            if self.policy_service.calculate_policy_hash(policy) != policy.hash \
                    or policy.state != ACTIVATED_STATE:
                invalid_policies.append(policy.policy_name)

        if invalid_policies:
            _LOG.error('Provided policies compromised or deleted')
            raise ModularApiBadRequestException(
                f'Provided policies compromised or deleted: '
                f'{", ".join(invalid_policies)}{line_sep}To get more detailed'
                f' information please execute command:{line_sep}'
                f'modular policy describe')

        warnings_list = []
        existed_policies = group_item.policies
        if action == 'add':
            existed_policies_in_group = set(policies).intersection(
                existed_policies)
            if existed_policies_in_group:
                warnings_list.append(
                    f'The following policies already attached to \'{group}\' '
                    f'group:{line_sep}'
                    f'{", ".join(existed_policies_in_group)}')
            group_item.policies = list(set(existed_policies).union(set(policies)))

        elif action == 'remove':
            not_existed_group_in_user = set(policies).difference(existed_policies)
            if not_existed_group_in_user:
                warnings_list.append(
                    f'The following policies does not attached to \'{group}\' '
                    f'group:{line_sep}{", ".join(not_existed_group_in_user)}')
            group_item.policies = list(set(existed_policies) - set(policies))
        else:
            raise ModularApiBadRequestException('Invalid action requested')

        group_item.last_modification_date = utc_time_now().isoformat()
        group_hash_sum = self.group_service.calculate_group_hash(group_item)
        group_item.hash = group_hash_sum
        self.group_service.save_group(group_item=group_item)

        result = 'added' if action == 'add' else 'deleted'

        _LOG.info(f'Policies: {", ".join(policies)} successfully {result}. '
                  f'Updated group: \'{group}\'')
        return CommandResponse(
            message=f'Policies: {", ".join(policies)} successfully {result}. '
                    f'Updated group: \'{group}\'',
            warnings=warnings_list)

    @staticmethod
    def check_group_items_exist(group_items: list) -> None:
        if not group_items:
            _LOG.error('Group(s) does not exist')
            raise ModularApiBadRequestException(
                'Group(s) does not exist. Please check spelling')

    def describe_group_handler(self, group: str, table_response,
                              json_response) -> CommandResponse:
        """
        Describes group content from ModularGroup table for specified group or
        list all existed groups
        :param group: Optional. group name which will be described
        :param table_response: output will be in table format
        :param json_response: output will be in json format
        :return: CommandResponse
        """

        if table_response and json_response:
            _LOG.error('Wrong parameters passed')
            raise ModularApiBadRequestException(
                'Please specify only one parameter - table or json')

        _LOG.info(f'Going to describe \'{group}\'')
        if group:
            existed_groups = self.group_service.describe_group(
                group_name=group)
        else:
            existed_groups = self.group_service.scan_groups()

        self.check_group_items_exist(group_items=existed_groups)  # todo fix bug
        existed_groups = existed_groups if not group else [existed_groups]
        pretty_groups = []
        invalid = 0
        for group in existed_groups:
            is_compromised = self.group_service.calculate_group_hash(
                group_item=group) != group.hash
            if is_compromised:
                invalid += 1

            pretty_user_item = {
                'Group name': group.group_name,
                'State': group.state,
                'Policy(ies)': group.policies,
                'Last modification date': convert_datetime_to_human_readable(
                    datetime_object=group.last_modification_date
                ),
                'Creation date': convert_datetime_to_human_readable(
                    datetime_object=group.creation_date
                ),
                'Consistency status': 'Compromised' if is_compromised else 'OK'
            }
            pretty_groups.append(pretty_user_item)
        valid_title = 'Group(s) description'
        compromised_title = f'Group(s) description{os.linesep}WARNING! ' \
                            f'{invalid} compromised group(s) have been detected.'

        if json_response:
            return CommandResponse(
                message=json.dumps(pretty_groups, indent=4)
            )
        return CommandResponse(
            table_title=compromised_title if invalid else valid_title,
            items=pretty_groups)

    def delete_group_handler(self, group: str) -> CommandResponse:
        """
        Delete group from ModularGroup table
        :param group: Group name to delete
        :return: CommandResponse
        """
        _LOG.info(f'Going to delete group \'{group}\'')
        group_item = self.group_service.describe_group(group_name=group)
        if not group_item:
            _LOG.error('Group does not exist')
            raise ModularApiBadRequestException(
                f'Group with name \'{group}\' does not exist')

        if group_item.state != ACTIVATED_STATE:
            _LOG.error(f'Group with name \'{group}\' is blocked or deleted')
            raise ModularApiBadRequestException(
                f'Group with name \'{group}\' is blocked or deleted. To get '
                f'more detailed information please execute command:{line_sep}'
                f'modular group describe --group {group}')
        self._check_group_in_users(group_name=group)
        if self.group_service.calculate_group_hash(group_item) != \
                group_item.hash:
            click.confirm(
                f'Group with name \'{group}\' is compromised. Command execution'
                f' leads to group entity hash sum recalculation. '
                f'Are you sure?', abort=True)

        group_item.state = REMOVED_STATE
        group_item.last_modification_date = utc_time_now().isoformat()
        group_hash_sum = self.group_service.calculate_group_hash(group_item)
        group_item.hash = group_hash_sum
        self.group_service.save_group(group_item=group_item)

        message = f'Group with name \'{group}\' successfully deleted'
        _LOG.info(message)
        return CommandResponse(message=message)

    def _check_group_in_users(self, group_name):
        users_with_specified_group = list(self.user_service.scan_users(
            filter_condition=User.groups.contains(group_name)))
        users_to_pay_attention = list()
        del_commands_list = str()
        if users_with_specified_group:
            for user in users_with_specified_group:
                if user.state != ACTIVATED_STATE:
                    continue
                users_to_pay_attention.append(user.username)
                del_commands_list += f'modular user remove_from_group ' \
                                     f'--username {user.username} --group ' \
                                     f'{group_name}{line_sep}'
        if users_to_pay_attention:
            raise ModularApiBadRequestException(
                f'Group with name \'{group_name}\' can not be deleted due to '
                f'it attachment to the following activated user(s): '
                f'{users_to_pay_attention}.{line_sep}'
                f'You should remove group \'{group_name}\' from each user in '
                f'{users_to_pay_attention} list first.{line_sep}'
                f'User(s) can be removed from group via command(s):{line_sep}'
                f'{del_commands_list}')

