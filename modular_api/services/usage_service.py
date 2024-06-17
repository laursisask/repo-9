import hashlib
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from pynamodb.pagination import ResultIterator

from bottle import LocalRequest

from modular_api.helpers.constants import (
    MODULES_DIR, API_MODULE_FILE, M_POINT, COMMAND,
    GROUP, DATE, META, STATUS, EVENT_TYPE, EVENT_TYPE_API, PRODUCT,
    JOB_ID, DATE_FORMAT, MODULE_NAME)
from modular_api.helpers.log_helper import get_logger
from modular_api.models.stats_model import Stats

_LOG = get_logger(__name__)


class AbstractUsageService(ABC):
    @abstractmethod
    def save_stats(self, request: LocalRequest, response: dict) -> None:
        """
        Method for statistic saving. Item to be saved template:
        api_stats_item = {
            "date": str,
            "mount_point": str,
            "group": str,
            "command": str,
            "meta": dict,
            "status": str,
            "event_type": str,
            "product": str,
            "timestamp": int,
            "id": str
        }

        async_job_stats_item = {
            "date": str,
            "mount_point": str,
            "meta": dict,
            "status": str,
            "event_type": str,
            "product": str,
            "job_id": str,
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
        self.modules_info = self.__get_installed_modules_info()
        self.last_rec_ts = None
        self.last_rec_date = None

    @staticmethod
    def _get_two_last() -> tuple[Stats | None, Stats | None]:
        items = tuple(Stats.type_timestamp_index.query(
            hash_key='CHAIN',
            scan_index_forward=False,
            limit=2
        ))
        match len(items):
            case 2:
                return items
            case 1:
                return items[0], None
            case _:
                return None, None

    @staticmethod
    def _get_last() -> Stats | None:
        return next(Stats.type_timestamp_index.query(
            hash_key='CHAIN',
            scan_index_forward=False,
            limit=1
        ), None)

    # class entity initialization helpers =====================================

    def __resolve_module_mount_point(self, request: LocalRequest) -> str:
        """
        Resolve mount point of module from the request. Obtained mount point is
        equal to mount points in Modular-API meta description.
        """
        raw_path = request.urlparts.path
        idx_of_second_slash = raw_path.find('/', 1)
        mount_point = raw_path[:idx_of_second_slash]
        mount_point_list = self.modules_info.keys()
        if mount_point not in mount_point_list:
            return '/'
        return mount_point

    @staticmethod
    def __start_month_ts(date: str, next_month=False) -> int:
        date_time = datetime.strptime(date, DATE_FORMAT).astimezone(
            timezone.utc)
        if not next_month:
            current_month_start = date_time.replace(day=1, hour=0, minute=0,
                                                    second=0, microsecond=0)
            return int(current_month_start.timestamp())
        if date_time.month == 12:
            next_month_start = date_time.replace(year=date_time.year + 1,
                                                 month=1, day=1, hour=0,
                                                 minute=0, second=0,
                                                 microsecond=0)
        else:
            next_month_start = date_time.replace(month=date_time.month + 1,
                                                 day=1, hour=0, minute=0,
                                                 second=0, microsecond=0)
        return int(next_month_start.timestamp())

    def __make_previous_item_id(self, date, timestamp):
        record, prev_record = self._get_two_last()
        record_ts = record.timestamp
        start_id = (self.__start_month_ts(date) + record_ts +
                    self.__start_month_ts(date, next_month=True))
        hex_hash = hashlib.md5(
            json.dumps(start_id, sort_keys=True).encode('utf-8')).hexdigest()
        if record.id == hex_hash:
            item_id = self.__start_month_ts(date) + record_ts + timestamp
        else:
            item_id = prev_record.timestamp + record_ts + timestamp
        item_id_hash = hashlib.md5(
            json.dumps(item_id, sort_keys=True).encode('utf-8')).hexdigest()
        return item_id_hash

    @staticmethod
    def __get_installed_modules_info() -> dict:
        """
        Return all Modular-API`s installed modules info
        installed_modules_info_model = {
        mount_point: module_name
        }
        """
        modules_path = Path(__file__).parent.parent / MODULES_DIR
        if not modules_path.exists():
            os.makedirs(modules_path)
        installed_modules_info = dict()
        for module in modules_path.iterdir():
            api_file_path = module / API_MODULE_FILE
            if not module.is_dir() or not api_file_path.exists():
                continue
            with open(api_file_path, 'r') as file:
                module_descriptor = json.load(file)
                mount_point = module_descriptor.get(M_POINT)
                module_name = module_descriptor.get(MODULE_NAME)
                installed_modules_info.update({mount_point: module_name})
        return installed_modules_info

    # make stats item =========================================================

    def __make_stats_item(self, mount_point, group, command, meta, status,
                          event_type, product, job_id):
        last = self._get_last()
        if last:
            self.last_rec_ts = last.timestamp
            self.last_rec_date = last.date

        utc_time_now = datetime.now(timezone.utc)
        ts = int(utc_time_now.timestamp()) * 1000
        date = utc_time_now.strftime(DATE_FORMAT)
        prev_item_id = None
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
            for key in [GROUP, COMMAND]:
                stats_doc.pop(key)
            stats_doc.update({JOB_ID: job_id})
        hex_hash = hashlib.md5(
            json.dumps(stats_doc, sort_keys=True).encode('utf-8')).hexdigest()
        current_ts = ts + (int(hex_hash, 16) % 1000)
        if current_ts == self.last_rec_ts:
            current_ts += 2
        stats_doc.update(timestamp=current_ts)
        if (not self.last_rec_date or
                (self.__start_month_ts(date) != self.__start_month_ts(
                    self.last_rec_date))):
            item_id = (self.__start_month_ts(date) + current_ts +
                       self.__start_month_ts(date, next_month=True))
        else:
            item_id = (self.last_rec_ts + current_ts +
                       self.__start_month_ts(date, next_month=True))
            prev_item_id = self.__make_previous_item_id(date=date,
                                                        timestamp=current_ts)
        hex_hash = hashlib.md5(
            json.dumps(item_id, sort_keys=True).encode('utf-8')).hexdigest()
        stats_doc.update(id=hex_hash)
        return stats_doc, current_ts, date, prev_item_id

    # main methods ============================================================

    def save_stats(self, request: LocalRequest, payload: dict) -> None:
        module_mount_point = self.__resolve_module_mount_point(request)
        parts = request.path.strip('/').split('/')
        if len(parts) >= 3:
            *_, group_name, command_name = parts
        elif len(parts) == 2:
            group_name, command_name = None, parts[1]
        else:
            group_name, command_name = None, None
        exec_status = payload.get(STATUS)
        meta = payload.get(META)
        event_type = payload.get(EVENT_TYPE)
        product = payload.get(PRODUCT)
        job_id = payload.get(JOB_ID)

        status = 'FAILED'
        if exec_status:
            status = 'SUCCESS' if exec_status.lower() == 'success' or \
                exec_status.lower() == 'succeeded' else 'FAILED'

        if not product:
            event_type = EVENT_TYPE_API
            product = self.modules_info.get(module_mount_point)

        stats_doc, current_event_ts, current_event_date, prev_item_id = (
            self.__make_stats_item(module_mount_point, group_name,
                                   command_name, meta, status, event_type,
                                   product, job_id))
        if prev_item_id:
            _LOG.info(f'Updating previous item. Item ID: {prev_item_id}')

            last = self._get_last()
            last.delete()
            last.id = prev_item_id
            last.save()

        _LOG.info(f'Saving usage event. Last timestamp: {self.last_rec_ts},'
                  f'current timestamp: {current_event_ts}')
        Stats(**stats_doc).save()
        _LOG.info(f'Usage event saved')

    def get_stats(self, module: str, from_date: int | None = None,
                  to_date: int | None = None) -> ResultIterator[Stats]:
        rkc = None
        if from_date and to_date:
            rkc &= Stats.timestamp.between(from_date, to_date)
        elif from_date:
            rkc &= (Stats.timestamp >= from_date)
        elif to_date:
            rkc &= (Stats.timestamp < to_date)
        return Stats.mount_point_timestamp_index.query(
            hash_key=module,
            range_key_condition=rkc
        )
