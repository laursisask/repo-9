from modular_api.services.group_service import GroupService
from modular_api.services.policy_service import PolicyService
from modular_api.services.user_service import UserService
from modular_api.services.audit_service import AuditService


class ServiceProvider:
    class __Services:
        # services
        __user_service = None
        __group_service = None
        __policy_service = None
        __audit_service = None

        def __str__(self):
            return id(self)

        def user_service(self):
            if not self.__user_service:
                self.__user_service = UserService()
            return self.__user_service

        def group_service(self):
            if not self.__group_service:
                self.__group_service = GroupService()
            return self.__group_service

        def policy_service(self):
            if not self.__policy_service:
                self.__policy_service = PolicyService()
            return self.__policy_service

        def audit_service(self):
            if not self.__audit_service:
                self.__audit_service = AuditService()
            return self.__audit_service

    instance = None

    def __init__(self):
        if not ServiceProvider.instance:
            ServiceProvider.instance = ServiceProvider.__Services()

    def __getattr__(self, item):
        return getattr(self.instance, item)
