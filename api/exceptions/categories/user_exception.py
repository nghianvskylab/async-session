from api.config.messages import ERROR_MESSAGES
from api.exceptions.base import ServerException
from fastapi import status


class _USER(ServerException):
    category = "USER"


class UserNotFound(_USER):
    detail = ERROR_MESSAGES["USER_NOT_FOUND"]
    status_code = status.HTTP_404_NOT_FOUND


class EmailAlreadyExists(_USER):
    detail = ERROR_MESSAGES["EMAIL_ALREADY_EXISTS"]
    status_code = status.HTTP_409_CONFLICT
