from typing import Any, Literal, TypedDict, Union, cast, get_args

from api.config.log import get_logger
from api.models.schema.misc.jsonable import JsonModel
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import Field
from typing_extensions import NotRequired

logger = get_logger("core")


ExceptionCategory = Literal[
    "INTERNAL_SERVER_ERROR",
    # NOTE: Careful about the difference between AUTHENTICATION and AUTHORIZATION
    "AUTHENTICATION",
    "AUTHORIZATION",
    "USER",
    "COMPANY",
    "PROJECT",
    "INFERENCE",
    "RESTRICTED",
    "UNIT",
    "VALIDATION",
]


class ErrorResponseDict(TypedDict):
    status_code: NotRequired[int]
    category: NotRequired[ExceptionCategory]
    headers: NotRequired[dict[str, str]]
    detail: NotRequired[str]


class IServerException(JsonModel):
    """
    Content of the error response.
    """

    reason: str
    """
    Exception class name.
    """
    category: ExceptionCategory
    detail: str


class _ServerExceptionMeta(type):
    _registry: dict[str, ErrorResponseDict] = {}
    """
    Place where all exceptions are listed.
    This value is used to generate OpenAPI documentation.
    """

    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        new_cls = super().__new__(cls, name, bases, attrs)

        if not name.startswith("_"):  # Exclude private classes
            base_attrs = new_cls._resolve_attrs(bases, attrs)
            excepted_info: dict[str, Any] = {}
            keyof_error_response: set[str] = {
                "status_code",
                "category",
                "headers",
                "detail",
            }
            for key in keyof_error_response:
                if key in base_attrs:
                    excepted_info[key] = base_attrs[key]
            if name in cls._registry:
                raise RuntimeError(f"Duplicate exception name: {name}")
            cls._registry[name] = cast(ErrorResponseDict, excepted_info)

        return new_cls

    def _resolve_attrs(
        cls, bases: tuple[type, ...], attrs: dict[str, Any]
    ) -> dict[str, Any]:
        resolved_attrs: dict[str, Any] = {}
        for base in bases:
            if isinstance(base, _ServerExceptionMeta):
                resolved_attrs.update(
                    base._resolve_attrs(
                        base.__bases__,
                        dict(base.__dict__),
                    )
                )
        resolved_attrs.update(attrs)
        # Remove private attributes
        for key in list(resolved_attrs.keys()):
            if key.startswith("_"):
                del resolved_attrs[key]
        return resolved_attrs

    def _get_errors_belong_to(
        cls,
        *,
        category: ExceptionCategory,
    ) -> dict[str, ErrorResponseDict]:
        return {
            name: info
            for name, info in cls._registry.items()
            if "category" in info and info["category"] == category
        }


class ServerException(HTTPException, metaclass=_ServerExceptionMeta):
    """Base class for all exceptions."""

    message: None = None
    """
    Message should be set in detail field.
    To avoid confusion, message field is set to None.
    """

    category: ExceptionCategory = "INTERNAL_SERVER_ERROR"
    detail: str = "Internal Server Error"
    status_code: int = 500
    headers: dict[str, str] = {}
    "NOTE: Header might be modified in the exception handler to inject CORS headers."

    def __init__(self, detail: str | None = None, debug: str | None = None) -> None:
        if debug:
            logger.exception(debug)
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers=self.headers,
        )

    def as_model(self) -> IServerException:
        return IServerException(
            reason=self.__class__.__name__,
            category=self.category,
            detail=self.detail,
        )

    def as_json_response(self, request: Request) -> JSONResponse:
        headers = self.headers
        if not str(self.status_code).startswith("2"):
            # Inject CORS headers to the failed response
            origin = request.headers.get("origin")
            cors_headers = {
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Credentials": "true",
            }
            headers = headers | cors_headers

        return JSONResponse(
            content=self.as_model().model_dump(mode="json"),
            status_code=self.status_code,
            headers=headers,
        )


common_category: set[ExceptionCategory] = {
    "INTERNAL_SERVER_ERROR",
    "RESTRICTED",
    "AUTHENTICATION",
    "USER",
    "UNIT",
    "COMPANY",
    "AUTHORIZATION",
    "VALIDATION",
}


def _new_preset(category: set[ExceptionCategory]) -> set[ExceptionCategory]:
    return common_category | category


preset_key = Literal[
    "uca",  # User, Company, Authorization
    "ucap",  # User, Company, Authorization, Project
    "ucapi",  # User, Company, Authorization, Project, Inference
]
exception_preset: dict[preset_key, set[ExceptionCategory]] = {
    "uca": common_category,
    "ucap": _new_preset({"PROJECT"}),
    "ucapi": _new_preset({"PROJECT", "INFERENCE"}),
}


def get_exceptions_schema(preset: preset_key) -> dict[int | str, dict[str, Any]]:
    exceptions: dict[str, ErrorResponseDict] = {}
    categories = tuple(exception_preset[preset])

    for c in categories or get_args(ExceptionCategory):
        exceptions.update(ServerException._get_errors_belong_to(category=c))

    schema: dict[int | str, dict[str, Any]] = {}

    for name, info in exceptions.items():
        assert "category" in info and "status_code" in info and "headers" in info
        status_code = info["status_code"]
        category = info["category"] if "category" in info else "INTERNAL_SERVER_ERROR"

        # Generate new basemodel for this exception to generate OpenAPI documentation
        new_fields = {
            "reason": (Literal[name], Field(...)),
            "category": (Literal[category], Field(...)),
        }
        # Create new Interface BaseModel class with single literal value fields
        new_server_exception_type = type(
            f"VI_{name}",  # Virtual Interface
            (IServerException,),
            {
                "__annotations__": {k: v[0] for k, v in new_fields.items()},
                **{k: v[1] for k, v in new_fields.items()},
            },
        )
        if status_code in schema and "model" in schema[status_code]:
            prev_model_type = schema[status_code]["model"]
            schema[status_code]["model"] = Union[
                prev_model_type,
                new_server_exception_type,
            ]
        else:
            schema[info["status_code"]] = {"model": new_server_exception_type}

    return schema
