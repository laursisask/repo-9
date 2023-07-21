import os

from pynamodb.attributes import UnicodeAttribute, JSONAttribute, \
    UTCDateTimeAttribute

from modular_api.models.base_model import BaseModel
from modular_api.helpers.date_utils import convert_datetime_to_human_readable


class Policy(BaseModel):
    class Meta:
        table_name = 'ModularPolicy'
        region = os.environ.get('AWS_REGION')

    policy_name = UnicodeAttribute(hash_key=True)
    policy_content = JSONAttribute()
    state = UnicodeAttribute()
    last_modification_date = UTCDateTimeAttribute(null=True)
    creation_date = UTCDateTimeAttribute(null=True)
    hash = UnicodeAttribute()

    def response_object_without_hash(self):
        return {
            'policy_name': self.policy_name,
            'policy_content': self.policy_content,
            'state': self.state,
            'last_modification_date': convert_datetime_to_human_readable(
                datetime_object=self.last_modification_date
            ),
            'creation_date': convert_datetime_to_human_readable(
                datetime_object=self.creation_date
            )
        }
