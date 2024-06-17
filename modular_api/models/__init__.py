import os

from modular_sdk.commons.helpers import classproperty
from modular_sdk.connections.mongodb_connection import MongoDBConnection
from modular_sdk.models.pynamodb_extension.base_model import \
    ABCMongoDBHandlerMixin, \
    RawBaseModel, RawBaseGSI
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel as ModularSafeUpdateModel
from modular_sdk.models.pynamodb_extension.pynamodb_to_pymongo_adapter import \
    PynamoDBToPyMongoAdapter

from modular_api.helpers.constants import ServiceMode, Env
from modular_api.services import SP


class ModularApiMongoDBHandlerMixin(ABCMongoDBHandlerMixin):

    @classmethod
    def mongodb_handler(cls):
        if not cls._mongodb:
            env = SP.env
            cls._mongodb = PynamoDBToPyMongoAdapter(
                mongodb_connection=MongoDBConnection(
                    mongo_uri=env.mongo_uri(),
                    default_db_name=env.mongo_database()
                )
            )
        return cls._mongodb

    @classproperty
    def is_docker(cls) -> bool:
        return os.getenv(Env.MODE, Env.MODE.default) in (ServiceMode.ONPREM,
                                                         ServiceMode.PRIVATE)


class BaseModel(ModularApiMongoDBHandlerMixin, RawBaseModel):
    pass


class BaseGSI(ModularApiMongoDBHandlerMixin, RawBaseGSI):
    pass


class BaseSafeUpdateModel(ModularApiMongoDBHandlerMixin,
                          ModularSafeUpdateModel):
    pass
