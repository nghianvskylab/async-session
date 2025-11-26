from api.exceptions.base import ServerException
from fastapi import status


class _ValidationError(ServerException):
    category = "VALIDATION"


class ValidationError(_ValidationError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
