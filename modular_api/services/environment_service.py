from typing import MutableMapping, Mapping

from modular_api.helpers.constants import Env, ServiceMode


class EnvironmentService:
    __slots__ = '_source',

    def __init__(self, source: MutableMapping):
        self._source = source

    def update_with(self, source: Mapping) -> None:
        self._source.update(source)

    def _ensure_env(self, name: Env) -> str:
        """
        Raises runtime error if the given env is not set
        :param name:
        :return:
        """
        if val := self._source.get(name.value):
            return val
        if name.default:
            return name.default
        raise RuntimeError(f'Env {name.value} is required')

    def secret_key(self) -> str:
        return self._ensure_env(Env.SECRET_KEY)

    def mode(self) -> ServiceMode:
        val = self._ensure_env(Env.MODE)
        try:
            return ServiceMode(val)
        except ValueError:
            return ServiceMode.SAAS

    def api_calls_per_second_limit(self) -> int:
        val = self._ensure_env(Env.API_CALLS_PER_SECOND_LIMIT)
        # if TypeError it's server configuration error, don't think we
        # should handle that case
        return int(val)

    def min_cli_version(self) -> str:
        return self._ensure_env(Env.MIN_CLI_VERSION)

    def is_private_mode_enabled(self) -> bool:
        return self._ensure_env(Env.ENABLE_PRIVATE_MODE).lower() in (
            'true', 'yes', 'y'
        )

    def mongo_uri(self) -> str:
        return self._ensure_env(Env.MONGO_URI)

    def mongo_database(self) -> str:
        return self._ensure_env(Env.MONGO_DATABASE)

    def mongo_rate_limits_database(self) -> str:
        return self._ensure_env(Env.MONGO_RATE_LIMITS_DATABASE)
