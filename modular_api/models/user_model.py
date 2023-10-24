import os

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, \
    ListAttribute, MapAttribute

from modular_api.models.base_model import BaseModel
from modular_api.helpers.date_utils import convert_datetime_to_human_readable


class User(BaseModel):
    class Meta:
        table_name = 'ModularUser'
        region = os.environ.get('AWS_REGION')

    username = UnicodeAttribute(hash_key=True)
    groups = ListAttribute()
    password = UnicodeAttribute()
    state = UnicodeAttribute()
    state_reason = UnicodeAttribute(null=True)
    last_modification_date = UTCDateTimeAttribute(null=True)
    creation_date = UTCDateTimeAttribute(null=True)
    meta = MapAttribute(null=True)
    hash = UnicodeAttribute()

    def response_object_without_hash(self):
        user_meta = {
            'username': self.username,
            'groups': self.groups,
            'password': self.password,
            'state': self.state,
            'state_reason': self.state_reason,
            'last_modification_date': convert_datetime_to_human_readable(
                datetime_object=self.last_modification_date
            ),
            'creation_date': convert_datetime_to_human_readable(
                datetime_object=self.creation_date
            )
        }
        if self.meta:
            user_meta.update({'meta': self.meta.as_dict()})
        return user_meta
