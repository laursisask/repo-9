from distutils.version import LooseVersion

from modular_api.helpers.exceptions import ModularApiBadRequestException
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger(__name__)


def check_version_compatibility(min_allowed_version: str,
                                current_version: str | None
                                ) -> list[str]:
    """
    Car raise in case version is incompatible
    :param min_allowed_version: from envs
    :param current_version: from cli
    :return: a list of warnings
    """
    if not current_version:
        _LOG.warning('modular cli did not send its version')
        return []
    m = LooseVersion(min_allowed_version)
    c = LooseVersion(current_version)
    if c.version[0] < m.version[0]:  # Major
        err = \
            f'CLI Major version {current_version} is lower than ' \
            f'minimal allowed {min_allowed_version}. Please, update ' \
            f'the Modular CLI to version greater than or equal to ' \
            f'{min_allowed_version}'
        _LOG.error(err)
        raise ModularApiBadRequestException(err)
    elif c.version[0] == m.version[0] and c.version[1] < m.version[1]:
        warn = \
            f'CLI Minor version {current_version} is lower than ' \
            f'the minimal required API version {min_allowed_version}. ' \
            f'Some features may not work. Consider updating the Modular ' \
            f'CLI to version greater than or equal to {min_allowed_version}'
        _LOG.warning(warn)
        return [warn]
    return []
