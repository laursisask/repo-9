import os

from pynamodb.attributes import UnicodeAttribute, ListAttribute, MapAttribute

from modular_api.helpers.constants import Env
from modular_api.helpers.date_utils import convert_datetime_to_human_readable
from modular_api.models import BaseModel
from modular_api.helpers.utilities import recursive_sort


class User(BaseModel):
    class Meta:
        table_name = 'ModularUser'
        region = os.environ.get(Env.AWS_REGION)

    username = UnicodeAttribute(hash_key=True)
    groups = ListAttribute(default=list)
    password = UnicodeAttribute()
    state = UnicodeAttribute()
    state_reason = UnicodeAttribute(null=True)
    last_modification_date = UnicodeAttribute(null=True)
    creation_date = UnicodeAttribute(null=True)
    meta = MapAttribute(default=dict)
    hash = UnicodeAttribute()

    def response_object_without_hash(self) -> dict:
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
        # Meta must be sorted as different order can generate different hash
        # deep sort for nested hash compatibility
        if self.meta:
            meta_dict = self.meta.as_dict()
            sorted_meta = recursive_sort(meta_dict)
            user_meta.update({'meta': sorted_meta})
        return user_meta
