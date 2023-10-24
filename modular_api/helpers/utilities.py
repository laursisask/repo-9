import os
import re
from datetime import datetime
from pathlib import Path

from .exceptions import ModularApiBadRequestException
from .log_helper import get_logger

_LOG = get_logger('utilities')


def is_path_exists(path: str, create_path: bool = True):
    """
    Check for path Existence;
    :param create_path: The boolean value.
    If not specified, path will be created
    :param path: the path to the destination
    :return: boolean value
    """
    if os.path.exists(path):
        return True

    if not os.path.exists(path) and create_path:
        try:
            os.makedirs(path)
            return True
        except OSError:
            _LOG.warning(
                f"No access: {path}. To find the log file, check "
                f"the directory from which you called the command"
            )
            return False
    else:
        return False


def prepare_request_path(path, prefix):
    if prefix:
        path = path.replace(prefix, '')
    return path


def parse_date(date):
    if date:
        try:
            return datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ModularApiBadRequestException(
                f'Expected date format: yyyy-mm-dd. Given value: {date}')


def validate_meta_keys(key):
    allowed_key_values = set()
    commands_base_path = Path(__file__).parent.parent.joinpath(
        'web_service/commands_base.json')
    with open(commands_base_path, 'r') as file:
        lines = file.readlines()
    for line in lines:
        match = re.search(r"(?<=\"name\": \").*(?=\",)", line)
        if match:
            allowed_key_values.add(match.group())
    if key not in allowed_key_values:
        raise ModularApiBadRequestException(
            f'Incorrect key name: \'{key}\'. Allowed values are only '
            f'parameters names from installed components, like \'tenant, '
            f'customer_id, region, etc.\'')


def token_from_auth_header(header: str) -> str:
    """
    Extracts token from bearer header
    """
    return header.split(maxsplit=2)[-1]
