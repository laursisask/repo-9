import json
import os

from pynamodb.attributes import UnicodeAttribute

from modular_api.helpers.constants import Env
from modular_api.helpers.date_utils import convert_datetime_to_human_readable
from modular_api.models import BaseModel


class Policy(BaseModel):
    class Meta:
        table_name = 'ModularPolicy'
        region = os.environ.get(Env.AWS_REGION)

    policy_name = UnicodeAttribute(hash_key=True)
    policy_content = UnicodeAttribute()  # json string
    state = UnicodeAttribute()
    last_modification_date = UnicodeAttribute(null=True)
    creation_date = UnicodeAttribute(null=True)
    hash = UnicodeAttribute()

    def response_object_without_hash(self):
        return {
            'policy_name': self.policy_name,
            'policy_content': self.content,
            'state': self.state,
            'last_modification_date': convert_datetime_to_human_readable(
                datetime_object=self.last_modification_date
            ),
            'creation_date': convert_datetime_to_human_readable(
                datetime_object=self.creation_date
            )
        }

    @property
    def content(self) -> list[dict]:
        return json.loads(self.policy_content)

    @content.setter
    def content(self, value: list[dict]) -> None:
        self.policy_content = json.dumps(value, sort_keys=True,
                                         separators=(',', ':'))
