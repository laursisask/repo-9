import binascii
import random
import re
import string
from hashlib import pbkdf2_hmac

from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.services import SP
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger(__name__)

ALLOWED_CHARS = string.ascii_letters + string.digits
PYTHON_PASSWORD_REGEX = re.compile(r'[A-Za-z0-9]{16,}')


def generate_password(size=16, chars=ALLOWED_CHARS):
    _LOG.debug('Generating random password')
    return ''.join(random.choice(chars) for _ in range(size))


def secure_string(string_to_secure: str) -> str:
    password_hash = pbkdf2_hmac(
        hash_name='sha256',
        password=string_to_secure.encode('utf-8'),
        salt=SP.env.secret_key().encode('utf-8'),
        iterations=1995,
        dklen=8
    )
    return binascii.hexlify(password_hash).decode()


def validate_password(password):
    _LOG.debug('Password validation')
    if not re.match(PYTHON_PASSWORD_REGEX, password):
        _LOG.info('Invalid password provided.')
        raise ModularApiBadRequestException(
            f'Invalid password provided. Password must contain more than 16 '
            f'chars. Allowed chars: {ALLOWED_CHARS}')
    return password
