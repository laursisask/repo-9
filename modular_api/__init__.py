from queue import Queue

from modular_api.services.usage_service import UsageService


class RequestQueue(Queue):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RequestQueue, cls).__new__(cls)
        return cls.instance


class StatisticService(UsageService):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(StatisticService, cls).__new__(cls)
        return cls.instance