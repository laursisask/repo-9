from datetime import datetime, timedelta, timezone

import jwt

from modular_api.helpers.exceptions import ModularApiUnauthorizedException
from modular_api.services import SP
from modular_api.web_service import META_VERSION_ID

EXPIRATION_IN_MINUTES = 60 * 24


def encode_data_to_jwt(username: str) -> str:
    return jwt.encode(
        {
            'username': username,
            'token_date': datetime.now(timezone.utc).isoformat(),
            'exp': datetime.now(timezone.utc) + timedelta(
                minutes=EXPIRATION_IN_MINUTES),
            'meta_version': META_VERSION_ID
        },
        SP.env.secret_key(),
        algorithm='HS256'
    )


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SP.env.secret_key(),
            algorithms='HS256'
        )
    except jwt.exceptions.ExpiredSignatureError:
        # if you are going to change text in next line - you must update
        # RELOGIN_TEXT variable in Modular-CLI to keep automated re-login
        raise ModularApiUnauthorizedException(
            'The provided token has expired. '
            'Please re-login to get a new token'
        )
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        return {}
    return payload


def username_from_jwt_token(token: str) -> str | None:
    # todo fix, sometimes this method can receive not jwt token but base64 encoded basic auth string (username:password)
    payload = decode_jwt_token(token)
    if username := payload.get('username'):
        return username
