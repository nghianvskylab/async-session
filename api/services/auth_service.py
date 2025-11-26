from typing import Optional

from api.config.database import NewSession
from api.exceptions.authorization import AdminRequired
from api.exceptions.categories.user_exception import UserNotFound
from api.models.schema.user import User, UserPermission
from api.services.user_service import UserService, get_user_service
from fastapi import Depends, Header, Request


async def get_auth_user(
    request: Request,
    session: NewSession,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Get authenticated user from header or query parameter."""
    user_id = x_user_id
    if not user_id:
        user_id_str = request.query_params.get("user_id")
        if user_id_str:
            try:
                user_id = int(user_id_str)
            except ValueError:
                raise UserNotFound("Invalid user_id format")
        else:
            raise UserNotFound(
                "user_id is required in header X-User-Id or query parameter"
            )

    # Use repository to get User model
    user = await user_service.repository.find_by_id(session, user_id)
    if not user:
        raise UserNotFound(f"IDが{user_id}のユーザーが見つかりません。")

    return user


async def only_admin(
    user: User = Depends(get_auth_user),
) -> User:
    """Check if the authenticated user is an admin."""
    if user.permission != UserPermission.ADMIN:
        raise AdminRequired()
    return user


async def check_admin(
    request: Request,
    session: NewSession,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", include_in_schema=False),
    user_service: UserService = Depends(get_user_service),
) -> None:
    """Ensure header/query user is admin for routes."""
    user_id = x_user_id
    if not user_id:
        user_id_str = request.query_params.get("user_id")
        if user_id_str:
            try:
                user_id = int(user_id_str)
            except ValueError:
                raise UserNotFound("Invalid user_id format")
        else:
            # If no user_id provided, skip admin check (for now, can be enabled later)
            return

    # Use repository to get User model
    user = await user_service.repository.find_by_id(session, user_id)
    if not user:
        raise UserNotFound(f"IDが{user_id}のユーザーが見つかりません。")

    if user.permission != UserPermission.ADMIN:
        raise AdminRequired()
