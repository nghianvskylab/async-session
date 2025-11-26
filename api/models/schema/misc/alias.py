from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Generic, TypedDict, TypeVar, cast, overload

from api.config.database import get_session
from api.config.log import get_logger
from api.models.schema.misc.jsonable import JsonModel
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped
from sqlalchemy.sql.expression import func
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing_extensions import NotRequired

_TableModel = TypeVar("_TableModel", bound=SQLModel)
_ModelSelect = TypeVar("_ModelSelect", bound=JsonModel)

logger = get_logger("database")


class SQLAPIModel(JsonModel, SQLModel):
    """
    Inherit `JsonModel`, and `SQLModel`.
    - `JsonModel` for serializing and deserializing
        to and from JSON with camelCase keys.
    - `SQLModel` for defining the model as a table in the database.
    """


_ColGetter = Callable[[], Any]


class _SQLAliasKnownCols(TypedDict):
    sort_column: NotRequired[_ColGetter]
    id_column: NotRequired[_ColGetter]
    is_deleted_column: NotRequired[_ColGetter]


class SQLAliasMixin(Generic[_TableModel]):
    """
    Place where common operations for communicating with the database are defined.
    """

    __known_cols__: ClassVar[_SQLAliasKnownCols | None] = None

    def __post_init__(self) -> None:
        pass

    @classmethod
    def get_id_column(cls) -> Mapped[Any] | None:
        if cls.__known_cols__ is None or "id_column" not in cls.__known_cols__:
            return None
        return col(cls.__known_cols__["id_column"]())

    @classmethod
    def get_sort_column(cls) -> Mapped[Any] | None:
        if cls.__known_cols__ is None or "sort_column" not in cls.__known_cols__:
            return None
        return col(cls.__known_cols__["sort_column"]())

    @classmethod
    def get_sort_column_by_name(cls, name: str | None) -> Any | None:
        if name is None:
            return None
        return getattr(cls, name, None)

    @classmethod
    def get_is_deleted_column(cls) -> Mapped[Any] | None:
        if cls.__known_cols__ is None or "is_deleted_column" not in cls.__known_cols__:
            return None
        return col(cls.__known_cols__["is_deleted_column"]())

    @overload
    @classmethod
    async def query_all(
        cls, session: AsyncSession, *, select_model: None = None
    ) -> Sequence[_TableModel]:
        ...

    @overload
    @classmethod
    async def query_all(
        cls, session: AsyncSession, *, select_model: type[_ModelSelect]
    ) -> Sequence[_ModelSelect]:
        ...

    @classmethod
    async def query_all(
        cls,
        session: AsyncSession,
        *,
        select_model: type[_ModelSelect] | None = None,
    ) -> Sequence[_TableModel] | Sequence[_ModelSelect]:
        selection = cls._resolve_select_model(select_model)
        statement = select(*selection)
        result = (await session.exec(statement)).all()
        return cast(Sequence[_TableModel] | Sequence[_ModelSelect], result)

    async def create(self, session: AsyncSession) -> _TableModel:
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return cast(_TableModel, self)

    async def update(self, session: AsyncSession) -> _TableModel:
        return await self.create(session)

    async def ensure_updated(self, session: AsyncSession) -> _TableModel:
        if not session.is_active:
            session.expunge(self)
            async with get_session() as _session:
                await self.update(_session)
        else:
            await self.update(session)
        return cast(_TableModel, self)

    async def refresh(self, session: AsyncSession) -> _TableModel:
        await session.refresh(self)
        return cast(_TableModel, self)

    async def delete(self, session: AsyncSession) -> None:
        await session.delete(self)
        await session.commit()

    @overload
    @classmethod
    async def find_by(
        cls,
        session: AsyncSession,
        *stmt: Any,
        select_model: None = None,
    ) -> _TableModel | None:
        ...

    @overload
    @classmethod
    async def find_by(
        cls,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect],
    ) -> _ModelSelect | None:
        ...

    @classmethod
    async def find_by(
        cls,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect] | None = None,
    ) -> _TableModel | _ModelSelect | None:
        selection = cls._resolve_select_model(select_model)
        statement = select(*selection).where(*stmt)
        result = (await session.exec(statement)).first()
        return cast(_TableModel | _ModelSelect | None, result)

    @overload
    @classmethod
    async def find_many_by(
        cls,
        session: AsyncSession,
        *stmt: Any,
        select_model: None = None,
    ) -> Sequence[_TableModel]:
        ...

    @overload
    @classmethod
    async def find_many_by(
        cls,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect],
    ) -> Sequence[_ModelSelect]:
        ...

    @classmethod
    async def find_many_by(
        cls,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect] | None = None,
    ) -> Sequence[_TableModel] | Sequence[_ModelSelect]:
        selection = cls._resolve_select_model(select_model)
        statement = select(*selection).where(*stmt)
        result = (await session.exec(statement)).all()
        return cast(Sequence[_TableModel] | Sequence[_ModelSelect], result)

    @overload
    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, id: str, *, select_model: None = None
    ) -> _TableModel:
        ...

    @overload
    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, id: str, *, select_model: type[_ModelSelect]
    ) -> _ModelSelect:
        ...

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        id: str,
        *,
        select_model: type[_ModelSelect] | None = None,
    ) -> _TableModel | _ModelSelect | None:
        """
        Get a record by its primary key.
        """
        inspected = inspect(cls)
        if inspected is None:
            raise ValueError("The model is not inspected.")
        pk_name = inspected.primary_key[0].name
        selection = cls._resolve_select_model(select_model)
        statement = select(*selection).where(getattr(cls, pk_name) == id)
        result = (await session.exec(statement)).first()
        return cast(_TableModel | _ModelSelect | None, result)

    @overload
    @classmethod
    async def get_many_by_ids(
        cls,
        session: AsyncSession,
        ids: Sequence[str],
        *,
        select_model: None = None,
    ) -> Sequence[_TableModel]:
        ...

    @overload
    @classmethod
    async def get_many_by_ids(
        cls,
        session: AsyncSession,
        ids: Sequence[str],
        *,
        select_model: type[_ModelSelect],
    ) -> Sequence[_ModelSelect]:
        ...

    @classmethod
    async def get_many_by_ids(
        cls,
        session: AsyncSession,
        ids: Sequence[str],
        *,
        select_model: type[_ModelSelect] | None = None,
    ) -> Sequence[_TableModel] | Sequence[_ModelSelect]:
        inspected = inspect(cls)
        if inspected is None:
            raise ValueError("The model is not inspected.")
        pk_name = inspected.primary_key[0].name
        selection = cls._resolve_select_model(select_model)
        statement = select(*selection).where(getattr(cls, pk_name).in_(ids))
        result = (await session.exec(statement)).all()
        return cast(Sequence[_TableModel] | Sequence[_ModelSelect], result)

    @classmethod
    async def length(
        cls,
        session: AsyncSession,
        *filter_condition: Any,
        column: Any,
    ) -> int:
        base_query = select(func.count(column))
        if filter_condition is not None:
            base_query = base_query.where(*filter_condition)

        result = (await session.exec(base_query)).first()

        return result if result is not None else 0

    @classmethod
    def _resolve_select_model(
        cls,
        select_model: type[_ModelSelect] | None,
        *,
        ignore_missing: bool = False,
    ) -> tuple[Any, ...]:
        root_model = cast(type[_TableModel], cls)
        if select_model is None:
            return (root_model,)

        select_fields = select_model.model_fields.keys()
        root_fields = root_model.model_fields.keys()

        if not set(select_fields).issubset(set(root_fields)) and not ignore_missing:
            raise ValueError(
                "select_model's fields must be a subset of "
                f"{root_model.__name__}'s fields."
            )

        intersect_fields = set(select_fields).intersection(set(root_fields))
        return tuple(getattr(root_model, field) for field in intersect_fields)
