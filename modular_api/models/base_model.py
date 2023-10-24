from datetime import datetime

from pynamodb import models
from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.exceptions import DoesNotExist
from pynamodb.expressions.condition import Condition
from typing import (Any, Optional, Dict, Sequence, Type, Text, Iterable, Union,
                    Iterator)
from pynamodb.models import _T, _KeyType
from pynamodb.pagination import ResultIterator

from modular_api.web_service.config import Config
from modular_api.models.pynamodb_to_tinydb_adapter import PynamoDBToTinyDBAdapter
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger('base_model')
CONFIG = Config()
TINYDB_HANDLER = None
if CONFIG.mode in ['onprem', 'private']:
    TINYDB_HANDLER = PynamoDBToTinyDBAdapter()


class BaseModel(models.Model):

    @classmethod
    def batch_get(
        cls: Type[_T],
        items: Iterable[Union[_KeyType, Iterable[_KeyType]]],
        consistent_read: Optional[bool] = None,
        attributes_to_get: Optional[Sequence[str]] = None,
    ) -> Iterator[_T]:
        if TINYDB_HANDLER:
            return TINYDB_HANDLER.tiny_batch_get(
                model_class=cls,
                items=items
            )
        return super().batch_get(items=items)

    @classmethod
    def query(cls: Type[_T], hash_key: _KeyType,
              range_key_condition: Optional[Condition] = None,
              filter_condition: Optional[Condition] = None,
              consistent_read: bool = False, index_name: Optional[str] = None,
              scan_index_forward: Optional[bool] = None,
              limit: Optional[int] = None,
              last_evaluated_key: Optional[Dict[str, Dict[str, Any]]] = None,
              attributes_to_get: Optional[Iterable[str]] = None,
              page_size: Optional[int] = None,
              rate_limit: Optional[float] = None) -> ResultIterator[_T]:
        if TINYDB_HANDLER:
            if page_size:
                limit = page_size
            return TINYDB_HANDLER.tiny_query(
                model_class=cls,
                hash_key=hash_key,
                filter_condition=filter_condition,
                range_key_condition=range_key_condition,
                limit=limit
            )
        return super().query(hash_key, range_key_condition, filter_condition,
                             consistent_read, index_name, scan_index_forward,
                             limit, attributes_to_get,
                             page_size, rate_limit)

    @classmethod
    def scan(cls: Type[_T], filter_condition: Optional[Condition] = None,
             segment: Optional[int] = None,
             total_segments: Optional[int] = None, limit: Optional[int] = None,
             last_evaluated_key: Optional[Dict[str, Dict[str, Any]]] = None,
             page_size: Optional[int] = None,
             consistent_read: Optional[bool] = None,
             index_name: Optional[str] = None,
             rate_limit: Optional[float] = None,
             attributes_to_get: Optional[Sequence[str]] = None) -> \
            ResultIterator[_T]:
        if TINYDB_HANDLER:
            return TINYDB_HANDLER.tiny_query(
                model_class=cls,
                filter_condition=filter_condition
            )
        return super().scan(filter_condition=filter_condition)

    @classmethod
    def get_nullable(cls, hash_key, range_key=None):
        if TINYDB_HANDLER:
            return TINYDB_HANDLER.get_nullable(model_class=cls,
                                               hash_key=hash_key,
                                               sort_key=range_key)
        try:
            return cls.get(hash_key, range_key)
        except DoesNotExist as e:
            _LOG.warning('The entity does not exist '
                         'with the following keys: Model:{0}; '
                         'hash_key:{1}; sort_key:{2}'.format(cls,
                                                             hash_key,
                                                             range_key))
            _LOG.warning(e.msg)
            return None

    @classmethod
    def get(cls: Type[_T], hash_key: _KeyType,
            range_key: Optional[_KeyType] = None,
            consistent_read: bool = False,
            attributes_to_get: Optional[Sequence[Text]] = None) -> _T:
        if TINYDB_HANDLER:
            return TINYDB_HANDLER.get(model_class=cls,
                                      hash_key=hash_key,
                                      range_key=range_key)
        return super().get(hash_key, range_key, consistent_read,
                           attributes_to_get)

    def delete(self, condition: Optional[Condition] = None) -> Any:
        if TINYDB_HANDLER:
            return TINYDB_HANDLER.delete(model_instance=self)
        return super().delete(condition)

    def save(self, condition: Optional[Condition] = None) -> Dict[str, Any]:
        if TINYDB_HANDLER:
            return TINYDB_HANDLER.save(model_instance=self)
        return super().save(condition)

    @classmethod
    def from_json(cls, model_json, attributes_to_get=None):
        if not model_json:
            return
        attributes_mapping = {}
        for attr_name, attr_body in cls._attributes.items():
            if attributes_to_get and attr_name in attributes_to_get:
                attributes_mapping.update({attr_body.attr_name: {attr_name}})
            elif not attributes_to_get:
                attributes_mapping.update({attr_body.attr_name: {'full_name': attr_name, 'type': attr_body}})

        cls_params = {}
        for short_name, attr_conf in attributes_mapping.items():
            full_name = attr_conf['full_name']
            value = model_json.get(short_name)
            if value and isinstance(attr_conf['type'], UTCDateTimeAttribute):
                value = datetime.fromtimestamp(value)
            cls_params.update({full_name: value})
        cls_instance = cls(**cls_params)
        return cls_instance
