import os
from functools import cached_property
from typing import TYPE_CHECKING

from modular_api.helpers.utilities import SingletonMeta

if TYPE_CHECKING:
    from modular_api.services.audit_service import AuditService
    from modular_api.services.environment_service import EnvironmentService
    from modular_api.services.group_service import GroupService
    from modular_api.services.policy_service import PolicyService
    from modular_api.services.usage_service import UsageService
    from modular_api.services.user_service import UserService


class ServiceProvider(metaclass=SingletonMeta):
    @cached_property
    def user_service(self) -> 'UserService':
        from modular_api.services.user_service import UserService
        return UserService()

    @cached_property
    def group_service(self) -> 'GroupService':
        from modular_api.services.group_service import GroupService
        return GroupService()

    @cached_property
    def policy_service(self) -> 'PolicyService':
        from modular_api.services.policy_service import PolicyService
        return PolicyService()

    @cached_property
    def audit_service(self) -> 'AuditService':
        from modular_api.services.audit_service import AuditService
        return AuditService()

    @cached_property
    def usage_service(self) -> 'UsageService':
        from modular_api.services.usage_service import UsageService
        return UsageService()

    @cached_property
    def env(self) -> 'EnvironmentService':
        from modular_api.services.environment_service import EnvironmentService
        return EnvironmentService(source=os.environ)
