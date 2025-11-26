from typing import Optional

from api.exceptions.categories.user_exception import EmailAlreadyExists, UserNotFound
from api.models.pageable import PagingModel, PagingQuery
from api.models.schema.user import (
    CreateUser,
    UpdateUser,
    User,
    UserDTO,
    UserDTOs,
    UserOrderColumn,
    UserPermission,
)
from api.repositories.user_repo import UserRepository
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession


class UserService:
    """Service for User business logic."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> UserDTO:
        """Get user by ID."""
        user = await self.repository.find_by_id(session, user_id)
        if not user:
            raise UserNotFound(f"IDが{user_id}のユーザーが見つかりません。")
        return await UserDTO.from_obj(user)

    async def get_user_by_email(self, session: AsyncSession, email: str) -> UserDTO:
        """Get user by email."""
        user = await self.repository.find_by_email(session, email)
        if not user:
            raise UserNotFound(f"Emailが{email}のユーザーが見つかりません。")
        return await UserDTO.from_obj(user)

    async def create_user(self, session: AsyncSession, new_user: CreateUser) -> UserDTO:
        """Create a new user."""
        exists_user = await self.repository.find_by_email(session, new_user.email)
        if exists_user:
            raise EmailAlreadyExists()

        created_user = User(
            name=new_user.name,
            email=new_user.email,
            permission=new_user.permission or UserPermission.USER,
            password=new_user.password or "",
        )

        # Save to database
        await self.repository.create(session, created_user)

        return await UserDTO.from_obj(created_user)

    async def get_users(
        self,
        session: AsyncSession,
        paging: PagingQuery[UserOrderColumn],
        permission: Optional[UserPermission] = None,
    ) -> PagingModel[UserDTOs]:
        """Get paginated list of users."""
        # Build query conditions
        query_stmt = self.repository.get_active_users_filters(permission)

        # Get paginated users
        users = await PagingModel[UserDTOs].from_page(
            session,
            *query_stmt,
            model=User,
            dto_model=UserDTOs,
            query=paging,
        )

        return users

    async def update_user(
        self,
        session: AsyncSession,
        user_id: int,
        update_data: UpdateUser,
    ) -> UserDTO:
        """Update a user."""
        user = await self.repository.find_by_id(session, user_id)
        if not user:
            raise UserNotFound(f"IDが{user_id}のユーザーが見つかりません。")

        if update_data.email and update_data.email != user.email:
            exists_user = await self.repository.find_by_email(
                session, update_data.email
            )
            if exists_user:
                raise EmailAlreadyExists()

        if update_data.name is not None:
            user.name = update_data.name
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.password is not None:
            user.password = update_data.password
        if update_data.permission is not None:
            user.permission = update_data.permission

        updated_user = await self.repository.update(session, user)

        return await UserDTO.from_obj(updated_user)

    async def delete_user(self, session: AsyncSession, user_id: int) -> None:
        """Soft delete a user."""
        user = await self.repository.find_by_id(session, user_id)
        if not user:
            raise UserNotFound(f"IDが{user_id}のユーザーが見つかりません。")

        # Soft delete
        await self.repository.soft_delete(session, user)


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
