import os

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, \
    ListAttribute
from modular_api.models.base_model import BaseModel


class Audit(BaseModel):
    class Meta:
        table_name = 'ModularAudit'
        region = os.environ.get('AWS_REGION')

    group = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)
    command = UnicodeAttribute()
    parameters = UnicodeAttribute(null=True)
    result = UnicodeAttribute(null=True)
    warnings = ListAttribute(null=True)
    hash_sum = UnicodeAttribute(attr_name='hash')

    def response_object_without_hash(self):
        return {
            'group': self.group,
            'timestamp': self.timestamp,
            'command': self.command,
            'parameters': self.parameters,
            'result': self.result,
            'warnings': self.warnings
        }
