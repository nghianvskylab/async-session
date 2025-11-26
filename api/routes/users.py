from typing import Annotated

from api.config.api_router import CoreAPIRoute
from api.config.database import NewSession
from api.config.decorator import log_input
from api.config.log import get_logger
from api.models.schema.user import UserDTO
from api.services.user_service import UserService, get_user_service
from fastapi import APIRouter, Depends

logger = get_logger("api.routes.user")

user_common_router = APIRouter(
    route_class=CoreAPIRoute,
)


async def get_user_dependency(
    user_id: int,
    session: NewSession,
    user_service: UserService = Depends(get_user_service),
) -> UserDTO:
    """Dependency to get user by ID using service layer."""
    return await user_service.get_user_by_id(session, user_id)


@user_common_router.get(
    "/{user_id}",
    description="ユーザー取得",
)
@log_input("UserRouter.get_user")
async def get_user(
    user: Annotated[UserDTO, Depends(get_user_dependency)],
) -> UserDTO:
    """Get user by ID."""
    return user
