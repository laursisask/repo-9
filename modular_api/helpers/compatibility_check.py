from distutils.version import LooseVersion
from helpers.log_helper import get_logger

from helpers.exceptions import ModularApiBadRequestException

_LOG = get_logger(__name__)


class CompatibilityChecker:
    @staticmethod
    def _resolve_received_version(cli_version):
        invalid_version_passed = 'Invalid version format passed. ' \
                                 'Expected the following: 3.67.1'
        try:
            major, minor, *_ = LooseVersion(cli_version).version
        except:
            _LOG.error(invalid_version_passed)
            raise ModularApiBadRequestException(invalid_version_passed)
        if not list(filter(lambda x: str(x).isdigit(), (major, minor))):
            _LOG.error(invalid_version_passed)
            raise ModularApiBadRequestException(invalid_version_passed)
        return major, minor

    def check_compatibility(self, request, allowed_version):
        warnings = []
        cli_version = request.headers.get('Cli-Version')
        if not cli_version:
            return
        major_allowed_version, minor_allowed_version = LooseVersion(
            allowed_version).version
        major_received_version, minor_received_version = \
            self._resolve_received_version(cli_version=cli_version)
        if major_allowed_version > major_received_version:
            major_version_error = \
                f'CLI Major version {major_received_version} is lower than ' \
                f'minimal allowed {major_allowed_version}. Please, update ' \
                f'the Modular CLI to version greater than or equal to ' \
                f'{allowed_version}'
            _LOG.error(major_version_error)
            raise ModularApiBadRequestException(major_version_error)
        elif minor_allowed_version > minor_received_version:
            minor_version_error = \
                f'CLI Minor version {minor_received_version} is lower than ' \
                f'the minimal required API version {minor_allowed_version}. ' \
                f'Some features may not work. Consider updating the Modular ' \
                f'CLI to version greater than or equal to {allowed_version}'
            _LOG.error(minor_version_error)
            warnings.append(minor_version_error)
        return warnings
