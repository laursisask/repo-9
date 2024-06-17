import json
from typing import Iterable

from modular_api.helpers.constants import ACTIVATED_STATE
from modular_api.helpers.date_utils import utc_time_now
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string
from modular_api.models.policy_model import Policy

_LOG = get_logger(__name__)


def validate_policy_item(item: dict) -> str | None:
    """
    Returns str in case there is an error
    :param item:
    :return:
    """
    if not isinstance(item.get('Effect'), str):
        return ('field \'Effect\' of type string is '
                'required for each policy item')
    if not isinstance(item.get('Module'), str):
        return ('field \'Module\' of type string is '
                'required for each policy item')
    if not isinstance(item.get('Resources'), list) or not all(
            [isinstance(v, str) for v in item.get('Resources')]):
        return ('field \'Resources\' of type list is '
                'required for each policy item')
    effect = item['Effect']
    effect_allowed = ('Allow', 'Deny')
    if effect not in effect_allowed:
        return (f'incorrect \'{effect}\' value provided for \'Effect\' key. '
                f'Allowed value: {", ".join(effect_allowed)}')
    resources = item['Resources']
    if not resources:  # empty list
        return ('resources property in policy can not be empty. To mark all '
                'resources use "*" symbol')
    for value in resources:
        if value.startswith('/'):
            return (
                f'resource name started with \'/\' not allowed. '
                f'Incorrect value: {value}'
            )
        if value.startswith(':'):
            return (
                f'resource name started with \':\' not allowed. '
                f'Incorrect value: {value}'
            )
        if value.startswith('*') and value != '*':
            return (
                f'resource name started with \'*\' not allowed. '
                f'Incorrect value: {value}. To Allow/Deny all in module`s '
                f'content use \'*\' or \'group:*\' or \'group\\subgroup:*\''
            )


def policy_validation(policy_content: list[dict]) -> None:
    """
    Raises ModularApiBadRequestException in case value is invalid
    :param policy_content:
    :return:
    """
    if not isinstance(policy_content, list) or not all(
            [isinstance(v, dict) for v in policy_content]):
        raise ModularApiBadRequestException(
            'Policy content should be a list of objects'
        )
    for i, item in enumerate(policy_content, start=1):
        error = validate_policy_item(item)
        if error:
            raise ModularApiBadRequestException(
                f'Invalid policy item number by index {i}: {error}'
            )


class PolicyService:
    @staticmethod
    def create_policy_entity(policy_name: str, policy_content: dict,
                             state: str = ACTIVATED_STATE):
        _LOG.info(f'Creating policy \'{policy_name}\'')
        return Policy(
            policy_name=policy_name,
            policy_content=json.dumps(policy_content, sort_keys=True,
                                      separators=(',', ':')),
            state=state,
            creation_date=utc_time_now().isoformat()
        )

    def extract_policies_names(self):
        # todo, remove, do not used this method
        return [policy.policy_name for policy in self.scan_policies()]

    @staticmethod
    def calculate_policy_hash(policy_item: Policy):
        _LOG.info(f'Calculating \'{policy_item.policy_name}\' policy hash ')
        prepared_user_to_be_hashed = json.dumps(
            policy_item.response_object_without_hash(),
            sort_keys=True
        )
        user_hash_sum = secure_string(prepared_user_to_be_hashed)
        return user_hash_sum

    @staticmethod
    def get_policies_by_name(policy_names: Iterable[str]) -> list[Policy]:
        _LOG.info(f'Batch get policies by provided names: '
                  f'{policy_names}')
        return list(Policy.batch_get(items=policy_names))

    @staticmethod
    def save_policy(policy_item: Policy) -> None:
        _LOG.info(f'Saving policy \'{policy_item.policy_name}\'')
        policy_item.save()

    @staticmethod
    def scan_policies() -> list[Policy]:
        _LOG.info('Scanning policies')
        # TODO do not use it and remove
        return list(Policy.scan())

    @staticmethod
    def describe_policy(policy_name: str) -> Policy | None:
        _LOG.info(f'Describing policy \'{policy_name}\'')
        return Policy.get_nullable(hash_key=policy_name)

    @staticmethod
    def delete_policy(policy_item: Policy) -> None:
        _LOG.info(f'Deleting policy \'{policy_item.policy_name}\'')
        policy_item.delete()
