import os

from pynamodb.attributes import UnicodeAttribute, ListAttribute

from modular_api.helpers.constants import Env
from modular_api.helpers.date_utils import convert_datetime_to_human_readable
from modular_api.models import BaseModel


class Group(BaseModel):
    class Meta:
        table_name = 'ModularGroup'
        region = os.environ.get(Env.AWS_REGION)

    group_name = UnicodeAttribute(hash_key=True)
    state = UnicodeAttribute()
    policies = ListAttribute(default=list)
    last_modification_date = UnicodeAttribute(null=True)
    creation_date = UnicodeAttribute(null=True)
    hash = UnicodeAttribute()

    def response_object_without_hash(self) -> dict:
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
