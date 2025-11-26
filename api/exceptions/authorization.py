from api.config.messages import ERROR_MESSAGES
from api.exceptions.base import ServerException
from fastapi import status


class _AUTHORIZATION(ServerException):
    category = "AUTHORIZATION"


class InvalidAuthorization(_AUTHORIZATION):
    detail = ERROR_MESSAGES["INVALID_AUTHORIZATION"]
    status_code = status.HTTP_401_UNAUTHORIZED


class AdminRequired(_AUTHORIZATION):
    detail = ERROR_MESSAGES["ADMIN_REQUIRED"]
    status_code = status.HTTP_403_FORBIDDEN
