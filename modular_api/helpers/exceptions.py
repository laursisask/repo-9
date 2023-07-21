from abc import ABC


class ModularApiBaseException(ABC, Exception):
    """
    Base exception
    """
    code: int


class ModularApiBadRequestException(ModularApiBaseException):
    """
    Incoming request to Modular-API is invalid due to parameters invalidity.
    """
    code = 400


class ModularApiConfigurationException(ModularApiBaseException):
    """
    Internal service is not configured: General configuration mismatch
    """
    code = 503


class ModularApiServiceTemporaryUnavailableException(ModularApiBaseException):
    """
    Internal service is not configured: General configuration mismatch
    """
    code = 503


class ModularApiUnauthorizedException(ModularApiBaseException):
    """
    CLI: provided credentials to AWS/Minio/Vault/MongoDB are invalid
    API: provided API credentials are invalid.
    """
    code = 401


class ModularApiForbiddenException(ModularApiBaseException):
    """
    The credentials are valid, but permission policy denies a command execution
    for requestor
    """
    code = 403


class ModularApiNotFoundException(ModularApiBaseException):
    """
    The requested resource has not been found
    """
    code = 404


class ModularApiTimeoutException(ModularApiBaseException):
    """
    Failed to respond in expected time range
    """
    code = 408


class ModularApiConflictException(ModularApiBaseException):
    """
    Incoming request processing failed due to environment state is incompatible
    with requested command
    """
    code = 409


class ModularApiReloginException(ModularApiBaseException):
    """
    "Marker" exception type for re-login initialization
    """
    code = 426


class ModularApiInternalException(ModularApiBaseException):
    """
    Admin failed to process incoming requests due to an error in the code.
    It’s a developer’s mistake.
    """
    code = 500


class ModularApiBadGatewayException(ModularApiBaseException):
    """
    Modular obtained the Error message from 3rd party application it is
    integrated with to satisfy the user's command.
    """
    code = 502


class ModularApiGatewayTimeoutException(ModularApiBaseException):
    """
    Should be raised in case admin did not get response from third party
    service (AWS service, Minio, Vault, MongoDB) requested in scope
    of the command execution.
    """
    code = 504


HTTP_CODE_EXCEPTION_MAPPING = {
    400: ModularApiBadRequestException,
    401: ModularApiUnauthorizedException,
    403: ModularApiForbiddenException,
    404: ModularApiNotFoundException,
    408: ModularApiTimeoutException,
    409: ModularApiConflictException,
    426: ModularApiReloginException,
    500: ModularApiInternalException,
    502: ModularApiBadGatewayException,
    503: ModularApiServiceTemporaryUnavailableException,
    504: ModularApiGatewayTimeoutException
}
