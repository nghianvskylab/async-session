from typing import Annotated, Optional

from api.config.api_router import CoreAPIRoute
from api.config.database import NewSession
from api.config.log import get_logger
from api.models.pageable import PagingModel, PagingQuery
from api.models.schema.user import (
    CreateUser,
    UserDTO,
    UserDTOs,
    UserOrderColumn,
    UserPermission,
)
from api.routes.users import user_common_router
from api.services.auth_service import check_admin
from api.services.user_service import UserService, get_user_service
from fastapi import APIRouter, Depends, Query

logger = get_logger("api.routes.admin.user")

admin_only_user_router = APIRouter(
    prefix="/users",
    tags=["Admin"],
    dependencies=[Depends(check_admin)],
    route_class=CoreAPIRoute,
)

# Include common routes (get user)
admin_only_user_router.include_router(user_common_router)


@admin_only_user_router.get(
    "",
    description="ユーザー一覧取得。admin専用",
)
async def get_users(
    session: NewSession,
    paging: Annotated[
        PagingQuery[UserOrderColumn], Depends(PagingQuery[UserOrderColumn])
    ],
    permission: Optional[UserPermission] = Query(
        None, description="Filter by permission"
    ),
    user_service: UserService = Depends(get_user_service),
) -> PagingModel[UserDTOs]:
    """Get list of users. Admin only."""
    return await user_service.get_users(session, paging, permission)


@admin_only_user_router.post(
    "",
    description="ユーザー作成。admin専用",
)
async def create_user(
    session: NewSession,
    new_user: CreateUser,
    user_service: UserService = Depends(get_user_service),
) -> UserDTO:
    """Create a new user. Admin only."""
    return await user_service.create_user(session, new_user)


users_router = APIRouter(
    route_class=CoreAPIRoute,
)

users_router.include_router(admin_only_user_router)
