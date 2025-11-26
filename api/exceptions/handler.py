import traceback

from api.config.log import get_logger
from api.exceptions.base import ServerException
from api.exceptions.categories.validator import ValidationError
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from pydantic_core import ValidationError as _ValidationError

logger = get_logger("core")


async def global_exception_handler(request: Request, exc: Exception) -> Response:
    traceback_log = traceback.format_exception(exc)
    logger.exception(traceback_log)

    # Convert all exceptions to ServerException
    if not isinstance(exc, ServerException):
        exc = ServerException()

    return exc.as_json_response(request)


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    traceback_log = traceback.format_exception(exc)
    logger.exception(traceback_log)

    if isinstance(exc, _ValidationError):
        errors = exc.errors()
        for error in errors:
            prefix = "Value error, "
            if error["msg"].startswith(prefix):
                prefix_length = len(prefix)
                error["msg"] = error["msg"][prefix_length:]
            # JSON serialization support
            if "ctx" in error and isinstance(error["ctx"], dict):
                error["ctx"] = {
                    k: str(v) for k, v in error["ctx"].items() if not isinstance(v, str)
                }
        # 最初のエラーのみ返却する
        message = errors[0]["msg"] if errors and "msg" in errors[0] else ""
        return ValidationError(message).as_json_response(request)
    else:
        return JSONResponse(
            content={"detail": "An unexpected error occurred"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
