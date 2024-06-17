from ddtrace import tracer
from unittest.mock import MagicMock
tracer.configure(writer=MagicMock())
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from modular_api.helpers.constants import Env, ServiceMode
from modular_api.helpers.password_util import secure_string
from modular_api.models.audit_model import Audit
from modular_api.models.group_model import Group
from modular_api.models.policy_model import Policy
from modular_api.models.stats_model import Stats
from modular_api.models.user_model import User
from modular_api.services import SP


class DBType(str, Enum):
    USERS = 'ModularUser'
    STATS = 'ModularStats'
    POLICIES = 'ModularPolicy'
    GROUPS = 'ModularGroup'
    AUDIT = 'ModularAudit'


LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'


def build_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(LOG_FORMAT))
    log.addHandler(h)
    return log


_LOG = build_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Patch tinydb to mongodb')
    parser.add_argument('--tinydb-root', type=Path,
                        default=str((Path.home() / '.modular_api/databases').resolve()),
                        help='Path where tinydb is (default: %(default)s)')
    parser.add_argument('--mongo-uri', type=str, required=True,
                        help='MongoDB full uri (mongodb://use...)')
    parser.add_argument('--mongo-database', type=str, required=True,
                        help='MongoDB database name')
    parser.add_argument('--secret-key', type=str, required=True,
                        help='Secret key that is used for service')
    parser.add_argument('--logging-filename', type=Path, required=False,
                        help='Filename to write logs to')

    return parser


def convert_user(item: dict) -> User:
    item['creation_date'] = datetime.fromtimestamp(item['creation_date'],
                                                   tz=timezone.utc).isoformat()
    user = User(**item)
    user.hash = SP.user_service.calculate_user_hash(user)
    return user


def convert_audit(item: dict) -> Audit:
    item['timestamp'] = datetime.fromtimestamp(item['timestamp'],
                                               tz=timezone.utc).isoformat()
    item.pop('hash', None)
    audit = Audit(**item)
    event_to_be_hashed = SP.audit_service.prepare_audit_to_be_hashed(audit=audit)
    event_to_be_hashed = json.dumps(event_to_be_hashed, sort_keys=True)
    audit.hash_sum = secure_string(event_to_be_hashed)
    return audit


def convert_group(item: dict) -> Group:
    item['creation_date'] = datetime.fromtimestamp(item['creation_date'],
                                                   tz=timezone.utc).isoformat()
    gr = Group(**item)
    gr.hash = SP.group_service.calculate_group_hash(gr)
    return gr


def convert_policy(item: dict) -> Policy:
    item['creation_date'] = datetime.fromtimestamp(item['creation_date'],
                                                   tz=timezone.utc).isoformat()
    item['policy_content'] = json.dumps(item['policy_content'],
                                        separators=(',', ':'))
    pol = Policy(**item)
    pol.hash = SP.policy_service.calculate_policy_hash(pol)
    return pol


def convert_stat(item: dict) -> Stats:
    item['type'] = 'CHAIN'
    return Stats(**item)


def patch_collection(data: dict, db_type: DBType) -> None:
    match db_type:
        case DBType.USERS:
            convertor = convert_user
        case DBType.POLICIES:
            convertor = convert_policy
        case DBType.AUDIT:
            convertor = convert_audit
        case DBType.STATS:
            convertor = convert_stat
        case DBType.GROUPS:
            convertor = convert_group
        case _:
            def convertor(x): return x
    _LOG.info('Converting items and saving to db')
    for item in (data.get('_default') or {}).values():
        convertor(item).save()


def patch(tinydb_root: Path, mongo_uri: str, mongo_database: str,
          secret_key: str, logging_filename: Path | None = None) -> None:
    if logging_filename:
        h = logging.FileHandler(logging_filename)
        h.setFormatter(logging.Formatter(LOG_FORMAT))
        _LOG.addHandler(h)
    os.environ[Env.MONGO_DATABASE.value] = mongo_database
    os.environ[Env.MONGO_URI.value] = mongo_uri
    os.environ[Env.SECRET_KEY.value] = secret_key
    os.environ[Env.MODE.value] = ServiceMode.ONPREM.value

    if not tinydb_root.is_dir() or not tinydb_root.exists():
        _LOG.error(f'{tinydb_root} must be a directory that exists')
        sys.exit(1)

    for filename in tinydb_root.iterdir():
        try:
            db_type = DBType(filename.stem)
        except ValueError:
            _LOG.warning(f'Not known db name: {filename.stem}')
            continue
        _LOG.info(f'Going to patch {filename.stem}')
        try:
            with open(filename, 'r') as fp:
                data = json.load(fp)
        except json.JSONDecodeError:
            _LOG.warning('Invalid JSON inside. Skipping')
            continue
        try:
            patch_collection(data, db_type)
        except Exception:
            _LOG.exception('Unexpected exception occurred. Ending patch')
            sys.exit(1)
        _LOG.info('Collection was patched')


def main():
    arguments = build_parser().parse_args()
    patch(**vars(arguments))


if __name__ == '__main__':
    main()
