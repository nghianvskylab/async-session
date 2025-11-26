from typing import Any, Literal, TypeVar

from alembic.autogenerate.api import AutogenContext
from pydantic import BaseModel
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeEngine

M = TypeVar("M")


class MutableModelMixin(Mutable):
    """
    Mutable model to trigger change events manually when the nested model is changed.
    """

    def __setattr__(self, name: str, value: Any) -> None:
        self.changed()
        return super().__setattr__(name, value)

    @classmethod
    def coerce(cls, key: str, value: BaseModel) -> Any:
        return value


class PydanticJsonType(TypeDecorator):
    """
    Custom SQLAlchemy TypeDecorator for Pydantic models.

    ```python
    class Model(BaseModel, MutableModelMixin):
        ...

    class ...
        model: Model | None = Field(
            default=None,
            sa_column=Column(PydanticJsonType.as_mutable(Model)),
    ```

    To make this work with Alembic's autogenerate, add the following to `env.py`:

    ```python
    context.configure(
        ...,
        render_item=PydanticJsonType.render_item,
    )
    ```
    """

    impl = JSON()
    hashable = False
    cache_ok = True

    def __init__(self, pydantic_type: type[MutableModelMixin], *args, **kwargs) -> None:
        if not issubclass(pydantic_type, BaseModel):
            raise TypeError("pydantic_type must be a subclass of pydantic")
        super().__init__(self, *args, **kwargs)
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(self.impl)  # type: ignore

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = value.model_dump_json()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = self.pydantic_type.model_validate_json(value)
        return value

    @classmethod
    def as_mutable(cls, pydantic_type: type[MutableModelMixin]) -> TypeEngine:
        return MutableModelMixin.as_mutable(cls(pydantic_type))

    @staticmethod
    def render_item(
        type_: str,
        obj: Any,
        autogen_context: AutogenContext,
    ) -> str | Literal[False]:
        if type_ == "type" and isinstance(obj, PydanticJsonType):
            return "sa.JSON()"

        # default rendering for other objects
        return False
