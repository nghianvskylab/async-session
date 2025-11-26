from collections.abc import Sequence
from typing import Any, Generic, Optional, TypeVar, cast, overload

from api.config.tz import now_dt
from api.models.schema.misc.alias import SQLAliasMixin
from api.models.schema.misc.jsonable import JsonModel
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.expression import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

_T = TypeVar("_T", bound=SQLAliasMixin)
_ModelSelect = TypeVar("_ModelSelect", bound=JsonModel)


class BaseRepository(Generic[_T]):
    def __init__(self, model: type[_T]):
        """Initialize repository with model class."""
        self.model = model

    async def find_by_id(
        self, session: AsyncSession, entity_id: int, include_deleted: bool = False
    ) -> Optional[_T]:
        """Find entity by ID."""
        id_column = getattr(self.model, "id", None)
        if id_column is None:
            raise AttributeError(f"{self.model.__name__} does not have a primary key")
        conditions = [id_column == entity_id]

        # Check for soft delete column
        is_deleted_column = self.model.get_is_deleted_column()
        if is_deleted_column is not None and not include_deleted:
            conditions.append(is_deleted_column.is_(None))

        return cast(
            Optional[_T],
            await self.model.find_by(session, *conditions),
        )

    @overload
    async def find_by(
        self,
        session: AsyncSession,
        *stmt: Any,
        select_model: None = None,
    ) -> Optional[_T]:
        ...

    @overload
    async def find_by(
        self,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect],
    ) -> Optional[_ModelSelect]:
        ...

    async def find_by(
        self,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect] | None = None,
    ) -> Optional[_T] | Optional[_ModelSelect]:
        """Find one entity by conditions."""
        return cast(
            Optional[_T] | Optional[_ModelSelect],
            await self.model.find_by(session, *stmt, select_model=select_model),
        )

    @overload
    async def find_many_by(
        self,
        session: AsyncSession,
        *stmt: Any,
        select_model: None = None,
    ) -> Sequence[_T]:
        ...

    @overload
    async def find_many_by(
        self,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect],
    ) -> Sequence[_ModelSelect]:
        ...

    async def find_many_by(
        self,
        session: AsyncSession,
        *stmt: Any,
        select_model: type[_ModelSelect] | None = None,
    ) -> Sequence[_T] | Sequence[_ModelSelect]:
        """Find many entities by conditions."""
        return cast(
            Sequence[_T] | Sequence[_ModelSelect],
            await self.model.find_many_by(session, *stmt, select_model=select_model),
        )

    @overload
    async def query_all(
        self, session: AsyncSession, *, select_model: None = None
    ) -> Sequence[_T]:
        ...

    @overload
    async def query_all(
        self, session: AsyncSession, *, select_model: type[_ModelSelect]
    ) -> Sequence[_ModelSelect]:
        ...

    async def query_all(
        self, session: AsyncSession, *, select_model: type[_ModelSelect] | None = None
    ) -> Sequence[_T] | Sequence[_ModelSelect]:
        """Query all entities."""
        return cast(
            Sequence[_T] | Sequence[_ModelSelect],
            await self.model.query_all(session, select_model=select_model),
        )

    @overload
    async def get_many_by_ids(
        self,
        session: AsyncSession,
        ids: Sequence[int],
        *,
        select_model: None = None,
    ) -> Sequence[_T]:
        ...

    @overload
    async def get_many_by_ids(
        self,
        session: AsyncSession,
        ids: Sequence[int],
        *,
        select_model: type[_ModelSelect],
    ) -> Sequence[_ModelSelect]:
        ...

    async def get_many_by_ids(
        self,
        session: AsyncSession,
        ids: Sequence[int],
        *,
        select_model: type[_ModelSelect] | None = None,
    ) -> Sequence[_T] | Sequence[_ModelSelect]:
        """Get many entities by IDs."""
        inspected = inspect(self.model)
        if inspected is None:
            raise ValueError("The model is not inspected.")
        pk_name = inspected.primary_key[0].name
        selection = self.model._resolve_select_model(select_model)
        statement = select(*selection).where(getattr(self.model, pk_name).in_(ids))
        result = (await session.exec(statement)).all()
        return cast(Sequence[_T] | Sequence[_ModelSelect], result)

    async def length(
        self,
        session: AsyncSession,
        *filter_condition: Any,
        column: Any | None = None,
    ) -> int:
        """Count entities with optional filter conditions."""
        if column is None:
            column = getattr(self.model, "id", None)
        if column is None:
            raise AttributeError(f"{self.model.__name__} does not have a primary key")

        base_query = select(func.count(column))
        if filter_condition:
            base_query = base_query.where(*filter_condition)

        result = (await session.exec(base_query)).first()
        return result if result is not None else 0

    async def create(self, session: AsyncSession, entity: _T) -> _T:
        """Create a new entity."""
        await entity.create(session)
        return entity

    async def update(self, session: AsyncSession, entity: _T) -> _T:
        """Update an entity."""
        await entity.update(session)
        return entity

    async def refresh(self, session: AsyncSession, entity: _T) -> _T:
        """Refresh an entity from database."""
        await entity.refresh(session)
        return entity

    async def soft_delete(self, session: AsyncSession, entity: _T) -> _T:
        """Soft delete an entity by setting deleted_at."""
        is_deleted_column = self.model.get_is_deleted_column()
        if is_deleted_column is None:
            raise ValueError(f"{self.model.__name__} does not support soft delete")

        if hasattr(entity, "deleted_at"):
            entity.deleted_at = now_dt()
        else:
            raise ValueError(
                f"{self.model.__name__} does not have deleted_at attribute"
            )

        await self.update(session, entity)
        return entity

    async def delete(self, session: AsyncSession, entity: _T) -> None:
        """Hard delete an entity."""
        await entity.delete(session)
