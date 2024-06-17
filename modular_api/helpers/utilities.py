import json
from datetime import datetime
from pathlib import Path
from collections import deque

from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger(__name__)


def parse_date(date):
    if date:
        try:
            return datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ModularApiBadRequestException(
                f'Expected date format: yyyy-mm-dd. Given value: {date}')


def validate_meta_keys(key: str) -> None:
    allowed_key_values = {*()}
    commands_base_path = Path(__file__).parent.parent.joinpath(
        'web_service/commands_base.json'
    )
    with open(commands_base_path, 'r') as file:
        data = json.load(file)

    queue = deque([data])
    while queue:
        node = queue.popleft()
        if isinstance(node, dict):
            for k, v in node.items():
                if k == 'name':
                    allowed_key_values.add(v)
                else:
                    queue.append(v)
        elif isinstance(node, list):
            queue.extend(node)

    if key not in allowed_key_values:
        raise ModularApiBadRequestException(
            f'Incorrect key name: \'{key}\'. Allowed values are only '
            f'parameters names from installed components, like \'tenant, '
            f'customer_id, region, etc.\''
        )


def token_from_auth_header(header: str) -> str:
    """
    Extracts token from bearer header
    """
    return header.split(maxsplit=2)[-1]


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def recursive_sort(item):
    if isinstance(item, dict):
        return {k: recursive_sort(v) for k, v in sorted(item.items())}
    if isinstance(item, list):
        return sorted([recursive_sort(v) for v in item])
    else:
        return item
