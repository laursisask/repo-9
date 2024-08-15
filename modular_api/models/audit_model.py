import os

from pynamodb.attributes import UnicodeAttribute, ListAttribute

from modular_api.helpers.constants import Env
from modular_api.helpers.date_utils import convert_datetime_to_human_readable
from modular_api.models import BaseModel


class Audit(BaseModel):
    class Meta:
        table_name = 'ModularAudit'
        region = os.environ.get(Env.AWS_REGION)

    group = UnicodeAttribute(hash_key=True)
    timestamp = UnicodeAttribute(range_key=True)
    command = UnicodeAttribute()
    parameters = UnicodeAttribute(null=True)
    result = UnicodeAttribute(null=True)
    warnings = ListAttribute(default=list)
    hash_sum = UnicodeAttribute(attr_name='hash')

    def response_object_without_hash(self) -> dict:
        return {
            'group': self.group,
            'timestamp': convert_datetime_to_human_readable(self.timestamp),
            'command': self.command,
            'parameters': self.parameters,
            'result': self.result,
            'warnings': self.warnings
        }
