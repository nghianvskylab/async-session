from collections.abc import Callable, Sequence
from typing import Any, ClassVar

from api.models.schema.misc.check import check_schema
from fastapi import FastAPI
from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)
from pydantic.alias_generators import to_camel as _to_camel
from pydantic.alias_generators import to_snake as _to_snake


def to_snake(s: Any) -> Any:
    match s:
        case str() as s:
            return _to_snake(s)
        case _:
            return s


def to_camel(s: Any) -> Any:
    match s:
        case str() as s:
            return _to_camel(s)
        case _:
            return s


def _round_trip_applying(
    val: dict[str, Any], func: Callable[[str], str]
) -> dict[str, Any]:
    applied: dict[str, Any] = {}
    for key, value in val.items():
        match value:
            case dict() as nested_val:
                applied[func(key)] = _round_trip_applying(nested_val, func)
            case list() | tuple() as nested_list:
                if nested_list and isinstance(nested_list[0], dict):
                    applied[func(key)] = [
                        _round_trip_applying(nested_val, func)
                        for nested_val in nested_list
                    ]
                else:
                    applied[func(key)] = nested_list
            case _:
                applied[func(key)] = value

    return applied


class JsonModel(BaseModel):
    """
    Model that serializes and deserializes to and from JSON with camelCase keys.
    This is applied to the model's fields recursively.
    """

    model_config: ClassVar[Any] = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    @model_serializer(mode="wrap", when_used="json")
    def ser_model(self, handler: SerializerFunctionWrapHandler):  # type: ignore
        # NOTE: Do not typehint this method, See below
        # https://github.com/fastapi/fastapi/discussions/10661#discussioncomment-8442889
        serialized = handler(self)
        return _round_trip_applying(serialized, to_camel)

    @model_validator(mode="before")
    @classmethod
    def val_model(cls, data: Any) -> Any:
        # If data is already a model instance (e.g., from_attributes), skip conversion
        if not isinstance(data, dict):
            # Return as is, let Pydantic handle it
            return data
        return _round_trip_applying(data, to_snake)

    def check(self) -> None:
        check_schema(self)


def refine_openapi_schema(
    app: FastAPI,
    extra_models: Sequence[type[JsonModel]] | None = None,
) -> None:
    """
    Convert all properties in the OpenAPI schema to camelCase.
    This should be called after all routes are added to the FastAPI app.
    """
    original_openapi_getter = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = original_openapi_getter()

        # Add extra models to the schema
        if extra_models:
            for model in extra_models:
                openapi_schema["components"]["schemas"][
                    model.__name__
                ] = model.model_json_schema()

        # Camelize all components in the schema
        schemas = openapi_schema["components"]["schemas"]
        for schema_name, schema in schemas.items():
            updated_properties: dict[str, Any] = {}
            for prop_name, prop in schema.get("properties", {}).items():
                updated_properties[to_camel(prop_name)] = prop

            if "enum" not in schema or updated_properties:
                schemas[schema_name]["properties"] = updated_properties

        app.openapi_schema = openapi_schema

        return app.openapi_schema

    setattr(app, "openapi", custom_openapi)
