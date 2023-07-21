import json
import os

from pydantic import BaseModel, validator, ValidationError

from modular_api.models.policy_model import Policy
from modular_api.helpers.constants import ACTIVATED_STATE
from modular_api.helpers.date_utils import utc_time_now
from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.password_util import secure_string

ERROR_LOCATION_KEY = 'loc'
ERROR_MESSAGE_KEY = 'msg'


class PolicyModel(BaseModel):
    Effect: str
    Module: str
    Resources: list

    @validator('Effect')
    def check_effect(cls, value):
        allowed_values = ['Allow', 'Deny']
        if value not in allowed_values:
            raise ModularApiBadRequestException(
                f'Incorrect \'{value}\' value provided for \'Effect\' key. '
                f'Allowed value: {", ".join(allowed_values)}')
        return value

    @validator('Resources')
    def check_resources(cls, values):
        if not values:
            raise ModularApiBadRequestException(
                'Resources property in policy can not be empty. To mark all '
                'resources use "*" symbol'
            )
        for value in values:
            if not isinstance(value, str):
                raise ModularApiBadRequestException(
                    f'Only String type values allowed in resources. '
                    f'Incorrect value: {value}'
                )
            if value.startswith('/'):
                raise ModularApiBadRequestException(
                    f'Resource name started with \'/\' not allowed. '
                    f'Incorrect value: {value}'
                )
            if value.startswith(':'):
                raise ModularApiBadRequestException(
                    f'Resource name started with \':\' not allowed. '
                    f'Incorrect value: {value}'
                )
            if value.startswith('*') and value != '*':
                raise ModularApiBadRequestException(
                    f'Resource name started with \'*\' not allowed. '
                    f'Incorrect value: {value}. To Allow/Deny all in module`s '
                    f'content use \'*\' or \'group:*\' or \'group\\subgroup:*\''
                )


def policy_validation(policy_content):
    for policy in policy_content:
        try:
            PolicyModel(**policy)
        except ValidationError as e:
            exception_message = f'Validation exception found for policy ' \
                                f'structure.{os.linesep}'
            error_locations = [e[ERROR_LOCATION_KEY][0] for e in e.errors()
                               if isinstance(e[ERROR_LOCATION_KEY], tuple)]
            error_messages = [e[ERROR_MESSAGE_KEY] for e in e.errors()]
            for validation_error in zip(error_locations, error_messages):
                pretty_exception = " ".join(validation_error)
                exception_message += pretty_exception + os.linesep
            raise ModularApiBadRequestException(exception_message)


_LOG = get_logger('policy_service')


class PolicyService:
    @staticmethod
    def create_policy_entity(policy_name, policy_content, state=None,
                             creation_date=None):
        _LOG.info(f'Going to create policy entity for {policy_name}')
        state = state if state else ACTIVATED_STATE
        creation_date = creation_date if creation_date else utc_time_now()
        return Policy(
            policy_name=policy_name,
            policy_content=policy_content,
            state=state,
            creation_date=creation_date
        )

    def extract_policies_names(self):
        return [policy.policy_name for policy in self.scan_policies()]

    @staticmethod
    def calculate_policy_hash(policy_item: Policy):
        _LOG.info(f'Going to calculate policy hash for '
                  f'{policy_item.policy_name} policy')
        prepared_user_to_be_hashed = json.dumps(
            policy_item.response_object_without_hash()
        )
        user_hash_sum = secure_string(prepared_user_to_be_hashed)
        return user_hash_sum

    @staticmethod
    def get_policies_by_name(policy_names):
        _LOG.info(f'Going to batch get policies by provided names: '
                  f'{policy_names}')
        return list(Policy.batch_get(items=policy_names))

    @staticmethod
    def save_policy(policy_item: Policy):
        _LOG.info(f'Going to save {policy_item.policy_name} policy entity')
        return Policy.save(policy_item)

    @staticmethod
    def scan_policies():
        _LOG.info('Going to scan policies')
        return list(Policy.scan())

    @staticmethod
    def describe_policy(policy_name):
        _LOG.info(f'Going to describe policy by {policy_name} name')
        return Policy.get_nullable(hash_key=policy_name)

    @staticmethod
    def delete_policy(policy_item: Policy):
        _LOG.info(f'Going to delete policy by {policy_item.policy_name} name')
        policy_item.delete()
