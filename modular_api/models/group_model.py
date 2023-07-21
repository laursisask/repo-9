import os

from pynamodb.attributes import UnicodeAttribute, ListAttribute, \
    UTCDateTimeAttribute

from modular_api.models.base_model import BaseModel
from modular_api.helpers.date_utils import convert_datetime_to_human_readable


class Group(BaseModel):
    class Meta:
        table_name = 'ModularGroup'
        region = os.environ.get('AWS_REGION')

    group_name = UnicodeAttribute(hash_key=True)
    state = UnicodeAttribute()
    policies = ListAttribute()
    last_modification_date = UTCDateTimeAttribute(null=True)
    creation_date = UTCDateTimeAttribute(null=True)
    hash = UnicodeAttribute()

    def response_object_without_hash(self):
        return {
            'group_name': self.group_name,
            'state': self.state,
            'policies': self.policies,
            'last_modification_date': convert_datetime_to_human_readable(
                datetime_object=self.last_modification_date
            ),
            'creation_date': convert_datetime_to_human_readable(
                datetime_object=self.creation_date
            )
        }
