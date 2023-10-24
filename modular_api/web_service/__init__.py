import hashlib
import os

WEB_SERVICE_PATH = os.path.dirname(__file__)
COMMANDS_BASE_FILE_NAME = 'commands_base.json'
META_VERSION_ID = ''


def _calculate_meta_hash():
    """"
    Write the SHA-1 hash of the commands_base.json file
    """
    global META_VERSION_ID
    h = hashlib.sha1()
    try:
        with open(os.path.join(WEB_SERVICE_PATH, COMMANDS_BASE_FILE_NAME), 'rb') as file:
            chunk = 0
            while chunk != b'':
                chunk = file.read(1024)
                h.update(chunk)
        META_VERSION_ID = h.hexdigest()
    except FileNotFoundError:
        pass


_calculate_meta_hash()
