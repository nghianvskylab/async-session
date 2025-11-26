from typing import Any, Optional

from api.models.schema.user import User, UserPermission
from api.repositories.base_repo import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession


class UserRepository(BaseRepository[User]):
    """Repository for User database operations."""

    def __init__(self) -> None:
        """Initialize UserRepository with User model."""
        super().__init__(User)

    async def find_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Find user by email."""
        deleted_column = self.model.get_is_deleted_column()
        filters: list[Any] = [self.model.email == email]
        if deleted_column is not None:
            filters.append(deleted_column.is_(None))
        return await self.find_by(
            session,
            *filters,
        )

    def get_active_users_filters(
        self,
        permission: Optional[UserPermission] = None,
    ) -> list[User]:
        """Get filter conditions for active users with optional permission filter.
        Returns list of conditions for query building.
        """
        deleted_column = self.model.get_is_deleted_column()
        conditions: list[Any] = []
        if deleted_column is not None:
            conditions.append(deleted_column.is_(None))
        if permission:
            conditions.append(self.model.permission == permission)
        return conditions
