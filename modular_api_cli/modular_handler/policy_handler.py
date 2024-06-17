import json
import os

import click

from modular_api.helpers.log_helper import get_logger
from modular_api.models.group_model import Group
from modular_api.helpers.constants import REMOVED_STATE, ACTIVATED_STATE
from modular_api.services.group_service import GroupService
from modular_api.services.policy_service import policy_validation, PolicyService
from modular_api.helpers.date_utils import convert_datetime_to_human_readable, utc_time_now
from modular_api.helpers.decorators import CommandResponse
from modular_api.helpers.exceptions import ModularApiBadRequestException, \
    ModularApiConflictException
from modular_api.helpers.file_helper import open_json_file

line_sep = os.linesep
_LOG = get_logger(__name__)


class PolicyHandler:
    def __init__(self, policy_service, group_service):
        self.policy_service: PolicyService = policy_service
        self.group_service: GroupService = group_service

    def add_policy_handler(self, policy: str, policy_path: str) -> CommandResponse:
        """
        Add policy to ModularPolicy table
        :param policy: Policy name
        :param policy_path: Path to file which contains allowed/denied actions
        :return: CommandResponse
        """
        _LOG.info(f'Going to add policy named \'{policy}\' from \'{policy_path}\'')
        existing_policy = self.policy_service.describe_policy(
            policy_name=policy
        )
        if existing_policy:
            if existing_policy.state == REMOVED_STATE:
                _LOG.error('Policy already exists')
                raise ModularApiBadRequestException(
                    f'Policy with name \'{policy}\' already exists and marked as '
                    f'\'{REMOVED_STATE}\'.')

            elif existing_policy.state == ACTIVATED_STATE:
                _LOG.error('Policy already exists')
                raise ModularApiBadRequestException(
                    f'Policy with name \'{policy}\' already exists. Please '
                    f'change name to another one or update existing '
                    f'\'{policy}\' policy with new permissions by command:'
                    f'{line_sep}modular policy update --policy {policy} '
                    f'--policy_path {policy_path}\'')

            _LOG.error('Policy already exists')
            raise ModularApiConflictException(
                f'Policy with name \'{policy}\' already exists with invalid '
                f'\'{existing_policy.state}\' state')

        policy_content = open_json_file(file_path=policy_path)
        policy_validation(policy_content=policy_content)
        policy_item = self.policy_service.create_policy_entity(
            policy_name=policy,
            policy_content=policy_content
        )

        policy_hash_sum = self.policy_service.calculate_policy_hash(
            policy_item=policy_item
        )
        policy_item.hash = policy_hash_sum
        self.policy_service.save_policy(policy_item=policy_item)

        _LOG.info('Policy successfully added')
        return CommandResponse(
            message=f'Policy with name \'{policy}\' successfully added')

    def update_policy_handler(self, policy: str, policy_path: str) -> CommandResponse:
        """
        Updates policy content in ModularPolicy table
        :param policy: Policy name which will be updated
        :param policy_path: Path to file which contains allowed/denied actions
        :return: CommandResponse
        """
        _LOG.info(f'Going to update policy \'{policy}\' from \'{policy_path}\'')
        policy_item = self.policy_service.describe_policy(policy_name=policy)
        if not policy_item:
            _LOG.error('Policy does not exist')
            raise ModularApiBadRequestException(
                f'Policy with name \'{policy}\' does not exist. Please check '
                f'policy name spelling or add new policy with name \'{policy}\''
                f' by command:{line_sep} modular policy add '
                f'--policy {policy} --policy_path {policy_path}')

        if policy_item.state != ACTIVATED_STATE:
            _LOG.error('Policy blocked or deleted')
            raise ModularApiBadRequestException(
                f'Policy with name \'{policy}\' is blocked or deleted. Can not '
                f'update policy content. To get more detailed info please '
                f'execute command:{line_sep} modular policy describe --policy '
                f'{policy}')

        if self.policy_service.calculate_policy_hash(policy_item) != \
                policy_item.hash:
            click.confirm(
                'Provided policy compromised. Command execution leads to policy '
                'entity hash sum recalculation. Are you sure?', abort=True)

        policy_content = open_json_file(file_path=policy_path)
        policy_validation(policy_content=policy_content)
        policy_item.content = policy_content
        policy_item.last_modification_date = utc_time_now().isoformat()

        policy_hash_sum = self.policy_service.calculate_policy_hash(
            policy_item=policy_item)
        policy_item.hash = policy_hash_sum
        self.policy_service.save_policy(policy_item=policy_item)

        _LOG.info('Policy successfully updated')
        return CommandResponse(
            message=f'Policy with name \'{policy}\' successfully updated')

    @staticmethod
    def check_policy_items_exist(policy_items: list) -> None:
        if not policy_items:
            raise ModularApiBadRequestException(
                'Policy(ies) not exists. To add policy please execute '
                '\'modular policy add\' command')

    def describe_policy_handler(self, policy: str, expand_view: bool,
                                json_response, table_response
                                ) -> CommandResponse:
        """
        Describes policy content from ModularPolicy table for specified name
        or list all existed policies
        :param expand_view: output will have more policy content
        :param policy: Optional. Policy name which will be described
        :param json_response: output will be in json format
        :param table_response: output will be in table format
        :return: CommandResponse
        """

        if table_response and json_response:
            _LOG.error('Wrong parameters passed')
            raise ModularApiBadRequestException(
                'Please specify only one parameter - table or json')

        _LOG.info(f'Going to describe policy \'{policy}\'')
        invalid = 0
        if policy:
            policy_items = self.policy_service.describe_policy(
                policy_name=policy)
        else:
            policy_items = self.policy_service.scan_policies()

        self.check_policy_items_exist(policy_items=policy_items)
        policy_items = policy_items if isinstance(policy_items, list) else [policy_items]
        pretty_policies = []
        for policy in policy_items:
            is_compromised = self.policy_service.calculate_policy_hash(
                policy_item=policy) != policy.hash
            if is_compromised:
                invalid += 1

            pretty_user_item = {
                'Policy Name': policy.policy_name,
                'Policy Content': policy.content,
                'State': policy.state,
                'Last Modification Date': convert_datetime_to_human_readable(
                    datetime_object=policy.last_modification_date
                ),
                'Creation Date': convert_datetime_to_human_readable(
                    datetime_object=policy.creation_date
                ),
                'Consistency status': 'Compromised' if is_compromised else 'OK'
            }
            if not expand_view:
                del pretty_user_item['Policy Content']
            pretty_policies.append(pretty_user_item)
        valid_title = 'Policy(ies) description'
        compromised_title = f'Policy(ies) description{os.linesep}WARNING! ' \
                            f'{invalid} compromised policy(ies) have been detected.'

        if json_response:
            return CommandResponse(
                message=json.dumps(pretty_policies, indent=4)
            )

        return CommandResponse(
            table_title=compromised_title if invalid else valid_title,
            items=pretty_policies)

    def delete_policy_handler(self, policy: str) -> CommandResponse:
        """
        Delete policy from ModularPolicy table
        :param policy: Policy name to delete
        :return: CommandResponse
        """
        _LOG.info(f'Going to delete policy \'{policy}\'')
        policy_item = self.policy_service.describe_policy(policy_name=policy)
        if not policy_item:
            _LOG.error('Policy does not exist')
            raise ModularApiBadRequestException(
                f'Policy with name \'{policy}\' does not exist. Nothing to '
                f'delete')

        if policy_item.state != ACTIVATED_STATE:
            _LOG.error('Policy blocked or deleted')
            raise ModularApiBadRequestException(
                f'Policy with name \'{policy}\' already blocked or deleted. '
                f'To get more detailed information please execute command:'
                f'{line_sep}modular policy describe --policy {policy}')

        if self.policy_service.calculate_policy_hash(policy_item) != \
                policy_item.hash:
            click.confirm(
                f'Policy with name {policy} is compromised. Command execution '
                f'leads to policy entity hash sum recalculation. Are you sure?',
                abort=True)

        self._check_policy_in_groups(policy_name=policy)
        policy_item.state = REMOVED_STATE
        policy_item.last_modification_date = utc_time_now().isoformat()
        policy_hash_sum = self.policy_service.calculate_policy_hash(
            policy_item=policy_item)
        policy_item.hash = policy_hash_sum
        self.policy_service.save_policy(policy_item=policy_item)

        _LOG.info('Policy successfully deleted')
        return CommandResponse(
            message=f'Policy with name \'{policy}\' successfully deleted')

    def _check_policy_in_groups(self, policy_name: str) -> None:
        all_groups_with_policy = list(self.group_service.scan_groups(
            filter_condition=Group.policies.contains(policy_name)
        ))

        groups_to_pay_attention = list()
        del_commands_list = str()
        for group in all_groups_with_policy:
            if group.state != ACTIVATED_STATE:
                continue
            groups_to_pay_attention.append(group.group_name)
            del_commands_list += f'modular group delete_policy ' \
                                 f'--policy {policy_name} --group ' \
                                 f'{group.group_name}{line_sep}'

        if groups_to_pay_attention:
            raise ModularApiBadRequestException(
                f'Policy with name \'{policy_name}\' can not be deleted due to '
                f'it existence in the following activated group(s): '
                f'{groups_to_pay_attention}.{line_sep}'
                f'You should remove policy \'{policy_name}\' from each group in '
                f'{groups_to_pay_attention} list first.{line_sep}'
                f'Policy can be deleted from group via command(s):{line_sep}'
                f'{del_commands_list}')
