from ddtrace import tracer
from unittest.mock import MagicMock
tracer.configure(writer=MagicMock())
import argparse
import json
import logging
import os
import sys
import time
from enum import Enum
from pathlib import Path

from modular_api.helpers.constants import Env, ServiceMode
from modular_api.helpers.password_util import secure_string
from modular_api.models.audit_model import Audit
from modular_api.models.group_model import Group
from modular_api.models.policy_model import Policy
from modular_api.models.user_model import User
from modular_api.services import SP

LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'


def build_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(LOG_FORMAT))
    log.addHandler(h)
    return log


_LOG = build_logger(__name__)


class DBType(str, Enum):
    USERS = 'ModularUser'
    # STATS = 'ModularStats'
    POLICIES = 'ModularPolicy'
    GROUPS = 'ModularGroup'
    AUDIT = 'ModularAudit'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Patch tinydb to mongodb')
    parser.add_argument('--secret-key', type=str, required=True,
                        help='Secret key that is used for service')
    parser.add_argument('--tables', nargs='+',
                        choices=[t.value for t in DBType],
                        required=True, type=DBType,
                        help='Table names to patch. Multiple can be specified')
    parser.add_argument('--pause', type=float, required=False, default=0,
                        help='Time in seconds to sleep after each write')
    parser.add_argument('--logging-filename', type=Path, required=False,
                        help='Filename to write logs to')

    return parser


def patch_users(pause: float = 0.0):
    for user in User.scan(rate_limit=1):
        _LOG.debug(f'Updating user {user.username}')
        user.update(actions=[
            User.hash.set(SP.user_service.calculate_user_hash(user))
        ])
        time.sleep(pause)


def patch_policies(pause: float = 0.0):
    for policy in Policy.scan(rate_limit=1):
        _LOG.debug(f'Updating policy {policy.policy_name}')
        policy.update(actions=[
            Policy.hash.set(SP.policy_service.calculate_policy_hash(policy))
        ])
        time.sleep(pause)


def patch_groups(pause: float = 0.0):
    for group in Group.scan(rate_limit=1):
        _LOG.debug(f'Updating group {group.group_name}')
        group.update(actions=[
            Group.hash.set(SP.group_service.calculate_group_hash(group))
        ])
        time.sleep(pause)


def patch_audit(pause: float = 0.0):
    for audit in Audit.scan(rate_limit=1):
        _LOG.debug('Updating some audit')
        event_to_be_hashed = SP.audit_service.prepare_audit_to_be_hashed(
            audit=audit)
        event_to_be_hashed = json.dumps(event_to_be_hashed, sort_keys=True)
        audit.update(actions=[
            Audit.hash_sum.set(secure_string(event_to_be_hashed))
        ])
        time.sleep(pause)


def patch_table(t: DBType, pause: float = 0.0):
    match t:
        case DBType.POLICIES:
            _LOG.info('Patching policies hash')
            patch_policies(pause)
        case DBType.GROUPS:
            _LOG.info('Patching groups hash')
            patch_groups(pause)
        case DBType.AUDIT:
            _LOG.info('Patching audit hash')
            patch_audit(pause)
        case DBType.USERS:
            _LOG.info('Patching users hash')
            patch_users(pause)


def patch(secret_key: str, tables: list[DBType], pause: float = 0.0,
          logging_filename: Path | None = None) -> None:
    if logging_filename:
        h = logging.FileHandler(logging_filename)
        h.setFormatter(logging.Formatter(LOG_FORMAT))
        _LOG.addHandler(h)
    _LOG.debug('Starting patch')

    os.environ[Env.MODE.value] = ServiceMode.SAAS.value
    os.environ[Env.SECRET_KEY.value] = secret_key
    try:
        for t in set(tables):
            patch_table(t, pause)
    except Exception:
        _LOG.exception('Unexpected error occurred. Ending patch')
        sys.exit(1)
    _LOG.info('Patch has finished')


def main():
    arguments = build_parser().parse_args()
    patch(**vars(arguments))


if __name__ == '__main__':
    main()
