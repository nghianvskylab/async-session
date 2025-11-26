from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from typing import Final, Optional

from api.config.tz import now_dt
from api.models.schema.base_dto import DTOsBase
from api.models.schema.misc.alias import SQLAliasMixin, SQLAPIModel
from api.models.schema.user_validator import (
    UserEmailStr,
    UserNameStr,
    UserPermissionEnum,
)
from sqlalchemy import DateTime, Index, text
from sqlmodel import Column, Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


class UserPermission(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls._value2member_map_


USER_ACLL: Final[dict[UserPermission, int]] = {
    UserPermission.ADMIN: 0,
    UserPermission.USER: 1,
}


class UserBase(SQLAPIModel):
    name: str = Field(index=True)
    email: str
    permission: UserPermission = Field(default=UserPermission.USER, index=True)
    password: str = Field(default="")


class User(UserBase, SQLAliasMixin, SQLModel, table=True):
    __tablename__ = "users"

    __known_cols__ = {
        "sort_column": lambda: User.created_at,
        "id_column": lambda: User.id,
        "is_deleted_column": lambda: User.deleted_at,
    }
    __table_args__ = (
        Index("idx_user_name_bigm", text("name gin_trgm_ops"), postgresql_using="gin"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=now_dt,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=now_dt,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=now_dt),
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class CreateUser(SQLAPIModel):
    email: UserEmailStr
    name: UserNameStr
    password: str
    permission: UserPermissionEnum


class UpdateUser(SQLAPIModel):
    email: UserEmailStr | None = None
    name: UserNameStr | None = None
    password: str | None = None
    permission: UserPermissionEnum | None = None


class UserOrderColumn(str, Enum):
    """Order columns for User pagination."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"
    EMAIL = "email"


class UserDTO(SQLAPIModel):
    id: int
    name: str
    email: str
    permission: UserPermission
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def from_obj(
        cls,
        model: "User",
        session: AsyncSession | None = None,
    ) -> "UserDTO":
        """Create UserDTO from User model."""
        default_keys = set(UserBase.model_fields.keys()) | set(cls.model_fields.keys())
        exclude_keys = {"password", "deleted_at"}

        return cls(
            **model.model_dump(include=default_keys - exclude_keys),
        )


class UserDTOs(DTOsBase[UserDTO]):
    """DTOs for User list response."""

    __dto__ = UserDTO
    items: list[UserDTO]

    @classmethod
    async def from_objs(cls, models: Sequence[UserDTO]) -> "UserDTOs":
        return cls(items=list(models))
