import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from modular_api.helpers.exceptions import ModularApiUnauthorizedException
from modular_api.helpers.log_helper import get_logger
from modular_api.helpers.constants import USERNAME_ATTR
from modular_api.web_service import META_VERSION_ID
from modular_api.web_service.config import Config

_LOG = get_logger(__name__)
EXPIRATION_IN_MINUTES = 60 * 24


def encode_data_to_jwt(username: str) -> str:
    return jwt.encode(
        {
            USERNAME_ATTR: username,
            'token_date': datetime.now(timezone.utc).isoformat(),
            'exp': datetime.now(timezone.utc) + timedelta(
                minutes=EXPIRATION_IN_MINUTES),
            'meta_version': META_VERSION_ID
        },
        Config().secret_passphrase,
        algorithm='HS256'
    )


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            Config().secret_passphrase,
            algorithms='HS256'
        )
    except jwt.exceptions.ExpiredSignatureError:
        # if you are going to change text in next line - you must update
        # RELOGIN_TEXT variable in Modular-CLI to keep automated re-login
        raise ModularApiUnauthorizedException(
            'The provided token has expired. Please re-login to get a new token')
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        return {}
    os.environ['AUDIT_MODULAR_CLI_USER'] = payload.get(
        USERNAME_ATTR)  # TODO, not safe to use it
    return payload


def username_from_jwt_token(token: str) -> Optional[str]:
    payload = decode_jwt_token(token)
    if USERNAME_ATTR in payload:
        return payload[USERNAME_ATTR]
