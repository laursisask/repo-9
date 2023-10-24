import json
import os.path
import shutil
from pathlib import Path

from modular_api.helpers.exceptions import ModularApiConfigurationException


def open_json_file(file_path, error_message=None):
    try:
        with open(file_path) as file:
            file_content = json.load(file)
        return file_content
    except Exception:
        if not error_message:
            error_message = 'Error occurred while opening file'
        raise ModularApiConfigurationException(error_message)


def save_json_file(file_path, file_content, error_message=None):
    try:
        with open(file_path, 'w') as file:
            json.dump(file_content, file)
    except Exception:
        if not error_message:
            error_message = 'Error occurred while saving file'
        raise ModularApiConfigurationException(error_message)


def resolve_policy_path():
    policies_path = os.path.join(str(Path.home()), '.modular', 'policies')
    if not os.path.isdir(policies_path):
        os.makedirs(policies_path)
    return policies_path


def remove_generated_policies(web_service_path):
    group_allowed_actions_mapping = os.path.join(
        web_service_path, 'group_allowed_actions_mapping.json')
    os.remove(group_allowed_actions_mapping)

    shutil.rmtree(resolve_policy_path(), ignore_errors=True)
