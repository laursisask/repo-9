import json

from modular_api.helpers.exceptions import ModularApiConfigurationException


def open_json_file(file_path, error_message=None):
    try:
        with open(file_path) as file:
            return json.load(file)
    except Exception:
        if not error_message:
            error_message = 'Error occurred while opening file'
        raise ModularApiConfigurationException(error_message)
