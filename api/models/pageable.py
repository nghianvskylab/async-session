from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from api.config.log import get_logger
from api.models.schema.base_dto import DTOsBase
from api.models.schema.misc.alias import SQLAliasMixin
from api.models.schema.misc.jsonable import JsonModel
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

logger = get_logger("database")

_OCT = TypeVar("_OCT", bound=Enum)


class PagingQuery(BaseModel, Generic[_OCT]):
    c: int = 1
    "Current page. -1の場合は全件を取得する"
    s: int = 10
    "Items per page"
    o: Literal["asc", "desc"] = "asc"
    "Order by"
    oc: _OCT | None = None
    "Order byの対象"


class PagingProperties(JsonModel):
    current_page: int
    total_pages: int
    total_items: int


_DTO = TypeVar("_DTO", bound=DTOsBase[Any])


class PagingModel(JsonModel, Generic[_DTO]):
    result: _DTO
    properties: PagingProperties

    @classmethod
    async def from_page(
        cls,
        session: AsyncSession,
        *stmt: Any,
        model: type[SQLAliasMixin[Any]],
        dto_model: type[_DTO],
        query: PagingQuery,
        join_models: list[tuple[Any, Any]] = [],
        sort_column: Any | None = None,
    ) -> "PagingModel[_DTO]":
        id_column = model.get_id_column()
        _sort_column = sort_column
        if _sort_column is None:
            _sort_column = model.get_sort_column_by_name(query.oc)
        if _sort_column is None:
            _sort_column = model.get_sort_column()

        if id_column is None or _sort_column is None:
            raise ValueError(
                "id_column and sort_column must be defined to use PagingModel"
            )

        is_deleted_column = model.get_is_deleted_column()

        if is_deleted_column is not None:
            if hasattr(is_deleted_column, "is_"):
                stmt = (*stmt, is_deleted_column.is_(None))
            else:
                stmt = (*stmt, is_deleted_column == False)

        statement_count = select(func.count()).select_from(model).where(*stmt)

        for right_model, on_clause in join_models:
            statement_count = statement_count.join(right_model, on_clause)

        total_items_result = await session.exec(statement_count)
        total_items = total_items_result.first()
        if total_items is None:
            total_items = 0

        current_page = query.c
        if current_page == -1:
            offset_value = 0
            limit_value = total_items
        else:
            # Calculate offset and limit for pagination
            offset_value = (current_page - 1) * query.s
            limit_value = query.s

        selection = model._resolve_select_model(dto_model.__dto__, ignore_missing=True)
        statement = select(*selection).where(*stmt)

        for right_model, on_clause in join_models:
            statement = statement.join(right_model, on_clause)

        statement = (
            statement.order_by(
                _sort_column.asc() if query.o == "asc" else _sort_column.desc()
            )
            .offset(offset_value)
            .limit(limit_value)
        )
        items_scalars = await session.exec(statement)
        restored_objects: list[JsonModel] = []

        for item in items_scalars.all():
            if dto_model.__dto__ is None:
                restored_objects.append(item)
            else:
                raw_dict: dict[str, Any] = {}
                for col, val in zip(selection, item):
                    raw_dict[col.name] = val
                restored_objects.append(dto_model.__dto__(**raw_dict))

        dtos = await dto_model.from_objs(restored_objects)

        return cls(
            result=dtos,
            properties=PagingProperties(
                current_page=current_page if current_page != -1 else 1,
                total_pages=(total_items + query.s - 1) // query.s
                if current_page != -1
                else 1,
                total_items=total_items,
            ),
        )
