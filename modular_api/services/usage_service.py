import json
import os
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from bottle import LocalRequest
from tinydb import TinyDB, Query

from modular_api.helpers.constants import (
    MODULES_DIR, API_MODULE_FILE, STATS_DB_NAME, M_POINT, TIMESTAMP, COMMAND,
    GROUP, DATE, META, STATUS, FIRST_REC_TIMESTAMP, EVENT_TYPE, EVENT_TYPE_API,
    PRODUCT, PRODUCT_MODULAR, JOB_ID)
from modular_api.helpers.log_helper import get_logger
from modular_api.models.pynamodb_to_tinydb_adapter import DATABASE_DIR, \
    LOG_FOLDER

_LOG = get_logger('usage_service')


class AbstractUsageService(ABC):
    @abstractmethod
    def save_stats(self, request: LocalRequest, response: dict) -> None:
        """
        Method for statistic saving. Item to be saved template:
        stats_item = {
            "date": str,
            "mount_point": str,
            "group": str,
            "command": str,
            "meta": dict,
            "status": str,
            "timestamp": int,
            "id": str
        }
        Pay attention: key order in dict must not be changed.
        """
        pass

    @abstractmethod
    def get_stats(self, module: str, from_date: int, to_date: int) -> list:
        """
        Method for statistic retrieving.
        """
        pass


class UsageService(AbstractUsageService):

    def __init__(self):
        pre_configured_user_dir = os.environ.get("M3MODULAR_USER_HOME")
        if pre_configured_user_dir:
            self.db_dir_path = os.path.join(
                pre_configured_user_dir, LOG_FOLDER, DATABASE_DIR)
        else:
            self.db_dir_path = os.path.join(
                str(Path.home()), LOG_FOLDER, DATABASE_DIR)
        if not os.path.exists(self.db_dir_path):
            os.makedirs(self.db_dir_path)
        self.db_file_path = os.path.join(self.db_dir_path, STATS_DB_NAME)
        self.db = TinyDB(self.db_file_path)
        self.query = Query()
        self.modules_list = self.__get_installed_modules()
        self.last_ts = self.__get_last_ts()

    # class entity initialization helpers =====================================

    def __resolve_module_mount_point(self, request: LocalRequest) -> str:
        """
        Resolve mount point of module from the request. Obtained mount point is
        equal to mount points in Modular-API meta description.
        """
        raw_path = request.urlparts.path
        idx_of_second_slash = raw_path.find('/', 1)
        mount_point = raw_path[:idx_of_second_slash]
        if mount_point not in self.modules_list:
            # todo to be discussed: what the module name we should return
            #  in case if mount point of module specified as "/" ?
            return '/'
        return mount_point

    def __get_last_ts(self) -> int:
        """
        Help method to place last event timestamp in RAM after Modular-API
        start.
        Purpose: avoid using the file system in constant read mode.
        """
        last_record_idx = len(self.db)
        last_record = self.db.get(doc_id=last_record_idx)
        if last_record:
            lr_ts = last_record.get(TIMESTAMP)
        else:
            lr_ts = FIRST_REC_TIMESTAMP
        return lr_ts

    @staticmethod
    def __get_installed_modules() -> list:
        """
        Return list of all Modular-API`s installed modules
        """
        modules_path = Path(__file__).parent.parent / MODULES_DIR
        if not modules_path.exists():
            os.makedirs(modules_path)
        installed_modules_list = list()
        for module in modules_path.iterdir():
            api_file_path = module / API_MODULE_FILE
            if not module.is_dir() or not api_file_path.exists():
                continue
            with open(api_file_path, 'r') as file:
                module_descriptor = json.load(file)
                installed_modules_list.append(module_descriptor.get(M_POINT))
        return installed_modules_list

    # make stats item =========================================================

    def __make_stats_item(self, mount_point, group, command, meta, status,
                          event_type, product, job_id):
        utc_time_now = datetime.now(timezone.utc)
        ts = int(utc_time_now.timestamp()) * 1000
        date = utc_time_now.strftime('%d-%m-%Y')
        stats_doc = {
            DATE: date,
            M_POINT: mount_point,
            GROUP: group,
            COMMAND: command,
            META: meta,
            STATUS: status,
            EVENT_TYPE: event_type,
            PRODUCT: product
        }
        if event_type != EVENT_TYPE_API:
            for key in [M_POINT, GROUP, COMMAND]:
                stats_doc.pop(key)
            stats_doc.update({JOB_ID: job_id})
        hex_hash = hashlib.md5(
            json.dumps(stats_doc, sort_keys=True).encode('utf-8')).hexdigest()
        current_ts = ts + (int(hex_hash, 16) % 1000)
        if current_ts == self.last_ts:
            current_ts += 2
        stats_doc.update(timestamp=current_ts)
        item_id = self.last_ts + current_ts
        hex_hash = hashlib.md5(
            json.dumps(item_id, sort_keys=True).encode('utf-8')).hexdigest()
        stats_doc.update(id=hex_hash)
        return stats_doc, current_ts
    
    def __resolve_payload(self, payload: dict):
        resolved_payload = {}
        resolved_payload['exec_status'] = payload.get('Status') \
            or payload.get('status') \
            or 'FAILED'
        resolved_payload['meta'] = payload.get('Meta') \
            or payload.get('meta')
        resolved_payload['event_type'] = payload.get('EventType') \
            or payload.get('event_type')
        resolved_payload['product'] = payload.get('Product') \
            or payload.get('product')
        resolved_payload['job_id'] = payload.get('JobId') \
            or payload.get('job_id')
        return resolved_payload

    # main methods ============================================================

    def save_stats(self, request: LocalRequest, payload: dict) -> None:
        module_mount_point = self.__resolve_module_mount_point(request)
        resolved_payload = self.__resolve_payload(payload)
        command_name = request.url_args.get(COMMAND)
        group_name = request.url_args.get(GROUP)
        exec_status = resolved_payload.get('exec_status')
        meta = resolved_payload.get('meta')
        event_type = resolved_payload.get('event_type')
        product = resolved_payload.get('product')
        job_id = resolved_payload.get('job_id')

        status = 'SUCCESS' if exec_status and \
                 exec_status.lower() == 'success' or \
                 exec_status.lower() == 'succeeded' else 'FAILED'

        if not event_type:
            event_type = EVENT_TYPE_API
            product = PRODUCT_MODULAR

        stats_doc, current_event_ts = self.__make_stats_item(
            module_mount_point, group_name, command_name, meta, status,
            event_type, product, job_id)
        _LOG.info(f'Saving usage event. Last timestamp: {self.last_ts},'
                  f'current timestamp: {current_event_ts}')
        self.db.insert(stats_doc)
        self.last_ts = current_event_ts
        _LOG.info(f'Usage event saved')

    def get_stats(self, module, from_date=None, to_date=None) -> list:
        if not from_date and not to_date:
            return self.db.search(self.query.mount_point == module)
        elif from_date and not to_date:
            return self.db.search(
                (self.query.mount_point == module) &
                (self.query.timestamp >= from_date))
        elif not from_date and to_date:
            return self.db.search(
                (self.query.mount_point == module) &
                (self.query.timestamp <= to_date))
        else:
            return self.db.search(
                (self.query.mount_point == module) &
                (self.query.timestamp >= from_date) &
                (self.query.timestamp <= to_date))
