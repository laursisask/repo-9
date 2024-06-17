import os

from pynamodb.attributes import UnicodeAttribute, MapAttribute, NumberAttribute
from pynamodb.indexes import AllProjection

from modular_api.helpers.constants import Env
from modular_api.models import BaseModel, BaseGSI


class TypeTimestampIndex(BaseGSI):
    class Meta:
        index_name = f'type-timestamp-index'
        projection = AllProjection()

    type = UnicodeAttribute(hash_key=True)
    timestamp = NumberAttribute(range_key=True)


class MountPointTimestampIndex(BaseGSI):
    class Meta:
        index_name = f'mount_point-timestamp-index'
        projection = AllProjection()

    mount_point = UnicodeAttribute(hash_key=True)
    timestamp = NumberAttribute(range_key=True)


class Stats(BaseModel):
    class Meta:
        table_name = 'ModularStats'
        region = os.environ.get(Env.AWS_REGION)

    id = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute()
    mount_point = UnicodeAttribute()
    group = UnicodeAttribute(null=True)
    command = UnicodeAttribute(null=True)
    job_id = UnicodeAttribute(null=True)
    meta = MapAttribute(null=True, default=None)
    status = UnicodeAttribute()
    event_type = UnicodeAttribute()
    product = UnicodeAttribute()
    timestamp = NumberAttribute()  # java timestamp
    type = UnicodeAttribute(default='CHAIN')

    type_timestamp_index = TypeTimestampIndex()
    mount_point_timestamp_index = MountPointTimestampIndex()
