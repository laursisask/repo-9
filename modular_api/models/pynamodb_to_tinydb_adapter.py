import os
from datetime import datetime
from pathlib import Path

from pynamodb.expressions.condition import Comparison, Between
from tinydb import TinyDB, Query

from modular_api.helpers.exceptions import ModularApiInternalException

M3MODULAR_DIR = '.modular_api'
DATABASE_DIR = 'databases'
D_M_Y_TEMPLATE = "%d.%m.%Y %H:%M:%S"
MILLIS_TEMPLATE = '%Y-%m-%dT%H:%M:%S.000000+0000'
BETWEEN = 'BETWEEN'
EQUAL = '='
MORE_OR_EQ = '>='
LESS_OR_EQ = '<='


class PynamoDBToTinyDBAdapter:
    def __init__(self):
        self.db_file_path = os.path.join(str(Path.home()), M3MODULAR_DIR,
                                         DATABASE_DIR)
        if not os.path.exists(self.db_file_path):
            os.makedirs(self.db_file_path)
        self.query_params = Query()

    def resolve_tiny_db_instance(self, model_class):
        collection_name = f'{model_class.Meta.table_name}.json'
        return TinyDB(os.path.join(self.db_file_path, collection_name))

    @staticmethod
    def __get_table_keys(model_class):
        short_to_body_mapping = {attr_body.attr_name: attr_body
                                 for attr_name, attr_body in
                                 model_class._attributes.items()}
        hash_key_name = None
        range_key_name = None
        for short_name, body in short_to_body_mapping.items():
            if body.is_hash_key:
                hash_key_name = short_name
                continue
            if body.is_range_key:
                range_key_name = short_name
                continue
        return hash_key_name, range_key_name

    def tiny_batch_get(self, model_class, items):
        tiny_db = self.resolve_tiny_db_instance(model_class=model_class)
        partition_key, range_key_name = self.__get_table_keys(model_class)
        query = self.query_params
        initial_query = None
        for item in items:
            if not initial_query:
                initial_query = (getattr(query, partition_key) == item)
            initial_query |= (getattr(query, partition_key) == item)
        result = [model_class.from_json(model_json=item)
                  for item in tiny_db.search(initial_query)]
        return result

    def tiny_query(self, model_class, filter_condition, limit=None,
                   range_key_condition=None, hash_key=None):
        tiny_db = self.resolve_tiny_db_instance(model_class=model_class)
        partition_key, range_key_name = self.__get_table_keys(model_class)
        initial_query = getattr(self.query_params, partition_key).exists()
        if all([filter_condition is None, range_key_condition is None, not hash_key]):
            return [model_class.from_json(model_json=item)
                    for item in tiny_db.search(initial_query)]
        condition = filter_condition
        if range_key_condition is not None:
            condition &= range_key_condition
        if isinstance(condition, (Comparison, Between)):
            condition = type('', (object,), {"values": [condition]})()
        result_query = self._convert_query(
            hash_key=hash_key, condition=condition, partition_key=partition_key,
            query=initial_query)

        return [model_class.from_json(model_json=item)
                for item in tiny_db.search(result_query)[:limit]]

    def _convert_query(self, hash_key, condition, partition_key, query):
        if hash_key:
            query &= self._query_mapping(
                operator=EQUAL,
                key=partition_key,
                value=hash_key)
        for item in condition.values:
            if item.operator == BETWEEN:
                query &= self._query_mapping(
                    operator=MORE_OR_EQ,
                    key=self._key_evaluate(item),
                    value=self._value_evaluate(item, 1)) & \
                    self._query_mapping(operator=LESS_OR_EQ,
                                        key=self._key_evaluate(item),
                                        value=self._value_evaluate(item, 2))
                continue
            query &= self._query_mapping(
                operator=item.operator,
                key=self._key_evaluate(item),
                value=self._value_evaluate(item, 1))

        return query

    @staticmethod
    def _key_evaluate(key):
        return key.values[0].attribute.attr_name

    @staticmethod
    def _value_evaluate(value, index):
        return value.values[index].value.get(value.values[index].attr_type)

    def _query_mapping(self, operator, key, value):
        query = self.query_params
        convert_map = {
            EQUAL: (getattr(query, key) == value),
            LESS_OR_EQ: (getattr(query, key)
                         <= self._date_to_milliseconds(value)),
            MORE_OR_EQ: (getattr(query, key)
                         >= self._date_to_milliseconds(value))
        }
        converted = convert_map.get(operator)
        if not converted:
            raise ModularApiInternalException(
                f'Unsupported operator type \'{operator}\'')
        return converted

    def get(self, model_class, hash_key, range_key=None):
        result = self.get_nullable(model_class=model_class,
                                   hash_key=hash_key,
                                   sort_key=range_key)
        if not result:
            raise model_class.DoesNotExist()
        return result

    def get_nullable(self, model_class, hash_key, sort_key=None):
        tiny_db = self.resolve_tiny_db_instance(model_class=model_class)
        hash_key_name, range_key_name = self.__get_table_keys(model_class)

        if not hash_key_name:
            raise ModularApiInternalException(
                'Can not identify the hash key name of '
                f'model: \'{type(model_class).__name__}\'')
        if sort_key and not range_key_name:
            raise ModularApiInternalException(
                f'The range key value is specified for '
                f'model \'{type(model_class).__name__}\' but there is no '
                f'attribute in the model marked as range_key')

        params = (self.query_params[hash_key_name] == hash_key)
        if range_key_name:
            params &= (self.query_params[range_key_name] == sort_key)

        raw_item = tiny_db.search(params)
        if raw_item:
            raw_item, *_ = raw_item
            return model_class.from_json(raw_item)

    def delete(self, model_instance):
        tiny_db = self.resolve_tiny_db_instance(model_class=model_instance)
        hash_key_name, range_key_name = self.__get_table_keys(model_instance)

        params = (self.query_params[hash_key_name] ==
                  model_instance.attribute_values[hash_key_name])
        if range_key_name:
            params &= (self.query_params[range_key_name] ==
                       model_instance.attribute_values[range_key_name])
        tiny_db.remove(params)

    def save(self, model_instance):
        tiny_db = self.resolve_tiny_db_instance(model_class=model_instance)
        self.delete(model_instance=model_instance)
        model_instance = self._datetime_serialization(model_instance)
        model_instance = self._attr_aliases_resolving(model_instance)
        tiny_db.insert(model_instance.attribute_values)

    @staticmethod
    def _datetime_serialization(model_instance):
        temp_instance = model_instance
        for attr in model_instance.attribute_values.items():
            attr_name, attr_value = attr
            if type(getattr(model_instance, attr_name)) is datetime:
                temp_instance.attribute_values[attr_name] = attr_value.timestamp()
        return temp_instance

    @staticmethod
    def _attr_aliases_resolving(model_instance):
        # needed for proper attribute name resolving for TinyDB
        # due to use custom attribute names in DynamoDB models
        if model_instance._dynamo_to_python_attrs:
            for k, v in model_instance._dynamo_to_python_attrs.items():
                if model_instance.attribute_values.get(v):
                    value = model_instance.attribute_values.pop(v)
                    model_instance.attribute_values[k] = value
        return model_instance

    @staticmethod
    def _date_to_milliseconds(date: str) -> float:
        try:
            date = datetime.strptime(date, MILLIS_TEMPLATE).timestamp()
        except ValueError:
            pass
        return date
